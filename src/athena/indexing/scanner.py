from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from pathspec import GitIgnoreSpec

from athena.cache import BoundedCache
from athena.config import AppConfig
from athena.domain import FileRecord, IndexedFileAnalysis, ScanReport
from athena.indexing.chunker import build_chunks
from athena.indexing.common import content_hash, language_for, stable_id
from athena.indexing.parsers import ParserRegistry
from athena.indexing.patterns import DERIVER_VERSION, ArchitectureDeriver
from athena.security import SecretDetector, WorkspaceGuard
from athena.storage import SQLiteStore

SCANNER_VERSION = "7"


@dataclass(frozen=True, slots=True)
class GitChanges:
    changed: frozenset[str]
    deleted: frozenset[str]


@dataclass(frozen=True, slots=True)
class _ParseRequest:
    absolute: Path
    relative: str
    size_bytes: int
    modified_ns: int
    old_hash: str | None


@dataclass(frozen=True, slots=True)
class _ParseOutcome:
    path: str
    analysis: IndexedFileAnalysis | None = None
    metadata_update: FileRecord | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None


class RepositoryScanner:
    def __init__(
        self,
        root: Path,
        config: AppConfig,
        store: SQLiteStore,
        analysis_cache: BoundedCache[tuple[object, ...], IndexedFileAnalysis] | None = None,
    ) -> None:
        self.guard = WorkspaceGuard(root, config.security.restrict_to_workspace)
        self.root = self.guard.root
        self.config = config
        self.store = store
        self.parsers = ParserRegistry(config.semantic)
        self.secrets = SecretDetector()
        self.analysis_cache = analysis_cache

    def file_snapshot(self) -> dict[str, tuple[int, int]]:
        """Return cheap source-file state for the daemon watcher."""
        snapshot: dict[str, tuple[int, int]] = {}
        for path in self._iter_files():
            try:
                stat = path.stat()
            except OSError:
                continue
            snapshot[path.relative_to(self.root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
        return snapshot

    def scan(self) -> ScanReport:
        started = time.perf_counter()
        repository_name, repository_id = repository_identity(self.root)
        previous_metadata = self.store.metadata()
        force_rescan = previous_metadata.get("scanner_version") != SCANNER_VERSION
        config_fingerprint = content_hash(
            json.dumps(
                {
                    "config": self.config.model_dump(mode="json"),
                    "local_knowledge": _local_knowledge_state(self.root),
                },
                sort_keys=True,
            )
        )
        current_commit = git_head(self.root)
        current_clean = git_is_clean(self.root) if current_commit is not None else False
        previous_commit = previous_metadata.get("indexed_commit")
        previous_worktree = previous_metadata.get("worktree_state")
        force_derivation = previous_metadata.get("deriver_version") != DERIVER_VERSION
        if (
            not force_rescan
            and not force_derivation
            and current_commit is not None
            and previous_commit == current_commit
            and previous_metadata.get("config_hash") == config_fingerprint
            and previous_worktree == "clean"
            and current_clean
        ):
            totals = self.store.stats()
            duration_ms = (time.perf_counter() - started) * 1000
            self.store.record_metric(
                "scan",
                repository_name,
                duration_ms,
                0,
                0,
                {"unchanged": totals["files"], "git_clean": True},
            )
            return ScanReport(
                repository_name,
                0,
                totals["files"],
                0,
                totals["chunks"],
                totals["nodes"],
                totals["edges"],
                round(duration_ms, 2),
                (),
            )
        incremental: GitChanges | None = None
        force_hash_validation = False
        if (
            not force_rescan
            and current_commit is not None
            and isinstance(previous_commit, str)
            and previous_commit != "working-tree"
            and previous_metadata.get("config_hash") == config_fingerprint
        ):
            if previous_worktree == "dirty" and current_clean and previous_commit == current_commit:
                # The worktree was restored without a commit. Git no longer lists which
                # paths differ from the indexed dirty representation, so validate all hashes.
                force_hash_validation = True
            else:
                incremental = git_changes(self.root, previous_commit, current_commit)
        current_paths: set[str] = set()
        scanned = unchanged = chunks_count = node_count = edge_count = 0
        warnings: list[str] = []
        failures: list[str] = []
        indexed_before = self.store.indexed_paths()
        requested_paths = set(incremental.changed) if incremental is not None else None
        requests: list[_ParseRequest] = []
        incremental_derivation = incremental is not None and not force_derivation
        pre_affected = (
            self.store.derived_owner_paths_touching(
                tuple(sorted(set(incremental.changed) | set(incremental.deleted)))
            )
            if incremental_derivation and incremental is not None
            else set()
        )
        successfully_replaced: set[str] = set()

        for absolute in self._iter_files(requested_paths):
            relative = absolute.relative_to(self.root).as_posix()
            current_paths.add(relative)
            stat = absolute.stat()
            old = self.store.file_state(relative)
            if (
                not force_rescan
                and not force_hash_validation
                and old is not None
                and int(old["size_bytes"]) == stat.st_size
                and int(old["modified_ns"]) == stat.st_mtime_ns
            ):
                unchanged += 1
                continue
            requests.append(
                _ParseRequest(
                    absolute,
                    relative,
                    stat.st_size,
                    stat.st_mtime_ns,
                    str(old["content_hash"]) if old is not None and not force_rescan else None,
                )
            )

        workers = self._worker_count(len(requests))
        batch_size = self.config.index.write_batch_size
        batches = 0
        if requests:
            with ThreadPoolExecutor(
                max_workers=workers, thread_name_prefix="athena-parser"
            ) as executor:
                for start in range(0, len(requests), batch_size):
                    request_batch = requests[start : start + batch_size]
                    outcomes = list(executor.map(self._parse_file, request_batch))
                    replacements = tuple(
                        outcome.analysis for outcome in outcomes if outcome.analysis is not None
                    )
                    metadata_updates = tuple(
                        outcome.metadata_update
                        for outcome in outcomes
                        if outcome.metadata_update is not None
                    )
                    self.store.replace_file_analyses(replacements, metadata_updates)
                    batches += 1
                    for outcome in outcomes:
                        warnings.extend(outcome.warnings)
                        if outcome.error:
                            failures.append(outcome.path)
                            warnings.append(outcome.error)
                        elif outcome.analysis is not None:
                            scanned += 1
                            successfully_replaced.add(outcome.path)
                            chunks_count += len(outcome.analysis.chunks)
                            node_count += len(outcome.analysis.nodes)
                            edge_count += len(outcome.analysis.edges)
                        else:
                            unchanged += 1

        if incremental is None:
            stale = indexed_before - current_paths
        else:
            # A changed path that is now ignored, unsupported, too large, or missing
            # must also lose its previous indexed representation.
            stale = set(incremental.deleted)
            stale.update((set(incremental.changed) - current_paths) & indexed_before)
        self.store.delete_files(tuple(sorted(stale)))

        self.store.cleanup_orphan_external_nodes()
        if incremental_derivation:
            affected = pre_affected | successfully_replaced | set(stale)
            affected.update(
                self.store.reference_owner_paths_for(tuple(sorted(successfully_replaced)))
            )
            derived_nodes, derived_edges = ArchitectureDeriver().derive(
                self.store, repository_id, repository_name, affected
            )
            derivation_mode = "incremental"
        else:
            affected = set(self.store.indexed_paths())
            derived_nodes, derived_edges = ArchitectureDeriver().derive(
                self.store, repository_id, repository_name
            )
            derivation_mode = "full"
        node_count += derived_nodes
        edge_count += derived_edges
        totals = self.store.stats()
        chunks_count = totals["chunks"]
        node_count = totals["nodes"]
        edge_count = totals["edges"]
        self.store.set_metadata("repository_id", repository_id)
        self.store.set_metadata("repository_name", repository_name)
        self.store.set_metadata("repository_root", str(self.root))
        if not failures:
            self.store.set_metadata("indexed_commit", current_commit or "working-tree")
            self.store.set_metadata("worktree_state", "clean" if current_clean else "dirty")
            self.store.set_metadata("scanner_version", SCANNER_VERSION)
            self.store.set_metadata("config_hash", config_fingerprint)
            self.store.set_metadata("deriver_version", DERIVER_VERSION)
            self.store.set_metadata("index_degraded", "false")
            self.store.set_metadata("failed_paths", "[]")
        else:
            self.store.set_metadata("index_degraded", "true")
            self.store.set_metadata("failed_paths", json.dumps(sorted(failures)))
        self.store.set_metadata("last_scan_epoch", str(int(time.time())))
        duration_ms = (time.perf_counter() - started) * 1000
        self.store.record_metric(
            "scan",
            repository_name,
            duration_ms,
            0,
            scanned,
            {
                "unchanged": unchanged,
                "deleted": len(stale),
                "warnings": len(warnings),
                "discovery": "git" if incremental is not None else "filesystem",
                "changed_candidates": len(incremental.changed) if incremental is not None else None,
                "workers": workers,
                "write_batches": batches,
                "failures": len(failures),
                "derivation_mode": derivation_mode,
                "derived_owners": len(affected),
            },
        )
        return ScanReport(
            repository_name,
            scanned,
            unchanged,
            len(stale),
            chunks_count,
            node_count,
            edge_count,
            round(duration_ms, 2),
            tuple(dict.fromkeys(warnings)),
        )

    def _worker_count(self, file_count: int) -> int:
        configured = self.config.index.parse_workers
        desired = configured or min(max((os.cpu_count() or 2) - 1, 1), 8)
        return max(1, min(desired, max(1, file_count)))

    def _parse_file(self, request: _ParseRequest) -> _ParseOutcome:
        try:
            raw = request.absolute.read_bytes()
            digest = content_hash(raw)
            language = language_for(request.absolute)
            record = FileRecord(
                request.relative,
                request.absolute,
                digest,
                request.size_bytes,
                request.modified_ns,
                language,
            )
            if request.old_hash == digest:
                return _ParseOutcome(request.relative, metadata_update=record)
            cache_key = (
                request.relative,
                digest,
                SCANNER_VERSION,
                self.config.index.chunk_lines,
                self.config.index.chunk_overlap_lines,
                self.config.index.secret_scan,
            )
            if self.analysis_cache is not None:
                cached = self.analysis_cache.get(cache_key)
                if cached is not None:
                    return _ParseOutcome(
                        request.relative,
                        IndexedFileAnalysis(record, cached.nodes, cached.edges, cached.chunks),
                    )
            parse_started = time.perf_counter()
            parse_warnings: list[str] = []
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
                parse_warnings.append(f"Decoded with replacement characters: {request.relative}")
            if self.config.index.secret_scan and self.secrets.contains_secret(text):
                text = self.secrets.redact(text)
                parse_warnings.append(
                    f"Sensitive-looking values were redacted before indexing: {request.relative}"
                )
            parser = self.parsers.parser_for(request.absolute)
            parsed = parser.analyze(request.relative, text, digest)
            tags = tuple(
                dict.fromkeys(
                    [
                        language,
                        *(
                            str(node.metadata.get("layer"))
                            for node in parsed.nodes
                            if node.metadata.get("layer")
                        ),
                        *(
                            str(framework)
                            for node in parsed.nodes
                            for framework in node.metadata.get("frameworks", [])
                        ),
                    ]
                )
            )
            chunks = build_chunks(
                request.relative,
                text,
                language,
                parsed.symbols,
                self.config.index.chunk_lines,
                self.config.index.chunk_overlap_lines,
                tags,
            )
            analysis = IndexedFileAnalysis(record, parsed.nodes, parsed.edges, chunks)
            if self.analysis_cache is not None:
                self.analysis_cache.put(
                    cache_key, analysis, (time.perf_counter() - parse_started) * 1000
                )
            return _ParseOutcome(
                request.relative,
                analysis,
                warnings=tuple([*parse_warnings, *parsed.warnings]),
            )
        except Exception as exc:
            return _ParseOutcome(
                request.relative,
                error=f"Failed to parse {request.relative}: {type(exc).__name__}: {exc}",
            )

    def _iter_files(self, relative_paths: set[str] | None = None) -> Iterator[Path]:
        ignore = self._ignore_spec()
        extensions = {ext.casefold() for ext in self.config.index.include_extensions}
        if relative_paths is not None:
            candidates: Iterator[Path] = (
                self.root / Path(value) for value in sorted(relative_paths)
            )
        else:
            candidates = self._walk_files(ignore)
        for path in candidates:
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved != self.root and self.root not in resolved.parents:
                continue
            relative = path.relative_to(self.root).as_posix()
            local_knowledge = relative.startswith(".athena/knowledge/")
            if (relative.startswith(".athena/") or relative == ".athena") and not local_knowledge:
                continue
            if not local_knowledge and ignore.match_file(relative):
                continue
            if path.suffix.casefold() not in extensions:
                continue
            try:
                if path.stat().st_size > self.config.index.max_file_bytes:
                    continue
            except OSError:
                continue
            yield path

    def _walk_files(self, ignore: GitIgnoreSpec) -> Iterator[Path]:
        """Walk source files while pruning ignored trees before entering them.

        ``Path.rglob`` visits every entry below large directories such as ``.git``,
        ``.venv`` and ``node_modules`` before Athena gets a chance to apply its ignore
        rules.  That is particularly expensive across Docker Desktop bind mounts.
        """
        for directory, dirnames, filenames in os.walk(self.root, followlinks=False):
            base = Path(directory)
            kept: list[str] = []
            for name in dirnames:
                relative = (base / name).relative_to(self.root).as_posix()
                local_knowledge = relative == ".athena" or relative.startswith(".athena/knowledge")
                athena_runtime = relative.startswith(".athena/") and not local_knowledge
                ignored = ignore.match_file(f"{relative}/") or ignore.match_file(
                    f"{relative}/.athena-walk-probe"
                )
                if not athena_runtime and not ignored:
                    kept.append(name)
            dirnames[:] = kept
            for name in filenames:
                yield base / name

    def _ignore_spec(self) -> GitIgnoreSpec:
        patterns = list(self.config.index.exclude_globs)
        gitignore = self.root / ".gitignore"
        if gitignore.is_file():
            patterns.extend(gitignore.read_text(encoding="utf-8", errors="ignore").splitlines())
        patterns.extend(
            [
                ".athena/index.db",
                ".athena/index.db-*",
                ".env",
                "**/*.pem",
                "**/*.key",
                "AGENTS.md",
                ".github/copilot-instructions.md",
                ".cursor/rules/**",
                ".vscode/mcp.json",
            ]
        )
        return GitIgnoreSpec.from_lines(patterns)


def repository_identity(root: Path) -> tuple[str, str]:
    name = root.name
    remote = _git(root, ["config", "--get", "remote.origin.url"])
    identity = remote or str(root.resolve())
    return name, stable_id("repo", identity)


def _local_knowledge_state(root: Path) -> list[tuple[str, int, int]]:
    directory = root / ".athena" / "knowledge"
    if not directory.is_dir():
        return []
    state: list[tuple[str, int, int]] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        state.append((path.relative_to(root).as_posix(), stat.st_size, stat.st_mtime_ns))
    return sorted(state)


def git_head(root: Path) -> str | None:
    return _git(root, ["rev-parse", "HEAD"])


def git_is_clean(root: Path) -> bool:
    """Return true only when Git is available and reports no tracked/untracked changes."""
    try:
        process = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    if process.returncode != 0:
        return False
    relevant = []
    for line in process.stdout.splitlines():
        path = line[3:].strip().strip('"').replace("\\", "/")
        if not _is_runtime_state(path):
            relevant.append(line)
    return not relevant


def git_changes(root: Path, indexed_commit: str, current_commit: str) -> GitChanges | None:
    """Return committed plus worktree changes relative to the indexed state.

    The result includes staged, unstaged, untracked, deleted, and renamed paths.
    ``None`` means Git discovery was unsafe and the caller must use a full scan.
    """
    committed = _git_name_status(
        root,
        ["diff", "--name-status", "-z", "--find-renames", indexed_commit, current_commit, "--"],
    )
    worktree = _git_name_status(
        root, ["diff", "--name-status", "-z", "--find-renames", current_commit, "--"]
    )
    untracked = _git_nul_paths(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    if committed is None or worktree is None or untracked is None:
        return None
    changed = set(committed.changed) | set(worktree.changed) | set(untracked)
    deleted = set(committed.deleted) | set(worktree.deleted)
    changed = {path for path in changed if not _is_runtime_state(path)}
    deleted = {path for path in deleted if not _is_runtime_state(path)}
    # Ignore rules affect repository-wide eligibility and require full reconciliation.
    if ".gitignore" in changed or ".gitignore" in deleted:
        return None
    return GitChanges(frozenset(changed - deleted), frozenset(deleted))


def _git_name_status(root: Path, args: list[str]) -> GitChanges | None:
    raw = _git_bytes(root, args)
    if raw is None:
        return None
    fields = [value.decode("utf-8", errors="replace") for value in raw.split(b"\0") if value]
    changed: set[str] = set()
    deleted: set[str] = set()
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if index >= len(fields):
            return None
        if status.startswith(("R", "C")):
            old_path = fields[index]
            index += 1
            if index >= len(fields):
                return None
            new_path = fields[index]
            index += 1
            changed.add(new_path)
            if status.startswith("R"):
                deleted.add(old_path)
        else:
            path = fields[index]
            index += 1
            if status.startswith("D"):
                deleted.add(path)
            else:
                changed.add(path)
    return GitChanges(frozenset(changed), frozenset(deleted))


def _git_nul_paths(root: Path, args: list[str]) -> set[str] | None:
    raw = _git_bytes(root, args)
    if raw is None:
        return None
    return {value.decode("utf-8", errors="replace") for value in raw.split(b"\0") if value}


def _git_bytes(root: Path, args: list[str]) -> bytes | None:
    try:
        process = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    return process.stdout if process.returncode == 0 else None


def _is_runtime_state(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized == ".athena/index.db"
        or normalized.startswith(".athena/index.db-")
        or normalized.startswith(".athena/daemon/")
    )


def _git(root: Path, args: list[str]) -> str | None:
    try:
        process = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    value = process.stdout.strip()
    return value if process.returncode == 0 and value else None
