from __future__ import annotations

import ctypes
import importlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena.config import AppConfig, load_config, state_directory
from athena.errors import AthenaError
from athena.indexing import RepositoryScanner
from athena.orchestrator import AthenaRuntime

Snapshot = dict[str, tuple[int, int]]
_ACTIVE_DAEMON_STATES = frozenset({"idle", "pending", "scanning", "degraded"})


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class FileChanges:
    added: frozenset[str] = frozenset()
    modified: frozenset[str] = frozenset()
    deleted: frozenset[str] = frozenset()

    @property
    def count(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(self.added | self.modified | self.deleted))


class PollingWatcher:
    """Portable filesystem watcher over Athena's exact indexable-file set."""

    def __init__(self, snapshot: Callable[[], Snapshot], *, initialize: bool = True) -> None:
        self._snapshot = snapshot
        self._previous = snapshot() if initialize else {}

    def poll(self) -> FileChanges:
        current = self._snapshot()
        previous_paths = set(self._previous)
        current_paths = set(current)
        changes = FileChanges(
            frozenset(current_paths - previous_paths),
            frozenset(
                path
                for path in previous_paths & current_paths
                if self._previous[path] != current[path]
            ),
            frozenset(previous_paths - current_paths),
        )
        self._previous = current
        return changes

    def refresh(self) -> None:
        self._previous = self._snapshot()


class ChangeCoalescer:
    def __init__(self, debounce_seconds: float, max_delay_seconds: float) -> None:
        self.debounce_seconds = debounce_seconds
        self.max_delay_seconds = max(max_delay_seconds, debounce_seconds)
        self._states: dict[str, str] = {}
        self._first_event: float | None = None
        self._last_event: float | None = None

    @property
    def pending_count(self) -> int:
        return len(self._states)

    def push(self, changes: FileChanges, now: float) -> None:
        if changes.count == 0:
            return
        if self._first_event is None:
            self._first_event = now
        self._last_event = now
        for path in changes.added:
            previous = self._states.get(path)
            self._states[path] = "modified" if previous == "deleted" else "added"
        for path in changes.modified:
            if self._states.get(path) != "added":
                self._states[path] = "modified"
        for path in changes.deleted:
            if self._states.get(path) == "added":
                self._states.pop(path)
            else:
                self._states[path] = "deleted"
        if not self._states:
            self._first_event = None
            self._last_event = None

    def ready(self, now: float) -> bool:
        if not self._states or self._first_event is None or self._last_event is None:
            return False
        return (
            now - self._last_event >= self.debounce_seconds
            or now - self._first_event >= self.max_delay_seconds
        )

    def flush(self) -> FileChanges:
        changes = FileChanges(
            frozenset(path for path, state in self._states.items() if state == "added"),
            frozenset(path for path, state in self._states.items() if state == "modified"),
            frozenset(path for path, state in self._states.items() if state == "deleted"),
        )
        self._states.clear()
        self._first_event = None
        self._last_event = None
        return changes


def daemon_paths(root: Path) -> dict[str, Path]:
    state = state_directory()
    directory = (state / "daemon") if state is not None else (root / ".athena" / "daemon")
    return {
        "directory": directory,
        "pid": directory / "daemon.pid",
        "stop": directory / "stop.requested",
        "status": directory / "status.json",
        "diagnostics": directory / "diagnostics.json",
        "log": directory / "daemon.log",
    }


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for attempt in range(5):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.02 * (attempt + 1))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        kernel32: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    return True


def _pid_is_athena_daemon(pid: int) -> bool:
    """Verify a POSIX PID belongs to Athena's daemon subprocess.

    PID files live in persistent state volumes.  After a container restart, Linux can reuse a
    recorded PID for the MCP server or an unrelated process; ``kill(pid, 0)`` alone is not a
    safe ownership check.
    """
    if not _pid_running(pid):
        return False
    if os.name == "nt":
        # Windows does not expose a dependency-free command-line inspection API here.  Active
        # status/heartbeat validation still rejects stopped or stale persisted daemon state.
        return True
    try:
        arguments = Path(f"/proc/{pid}/cmdline").read_bytes().decode().split("\0")
    except OSError:
        return False
    return _arguments_are_athena_daemon(arguments)


def _arguments_are_athena_daemon(arguments: list[str]) -> bool:
    """Recognize both ``python -m athena.cli`` and the installed console script."""
    module_entry = "athena.cli" in arguments
    console_entry = any(Path(argument).name == "athena" for argument in arguments[:2])
    return (module_entry or console_entry) and "daemon" in arguments and "run" in arguments


def _has_active_daemon_lock(root: Path, status: dict[str, Any] | None = None) -> bool:
    """Return whether the persistent lock belongs to a running Athena daemon."""
    current = status or load_daemon_status(root)
    pid = current.get("pid")
    if not isinstance(pid, int) or current.get("state") not in _ACTIVE_DAEMON_STATES:
        return False
    if not daemon_paths(root)["pid"].is_file():
        return False
    return _pid_is_athena_daemon(pid)


def _clear_stale_daemon_lock(root: Path, *, reclaim_pid: int | None = None) -> None:
    """Remove only reclaimable daemon-control files; preserve logs and diagnostics."""
    status = load_daemon_status(root)
    if _has_active_daemon_lock(root, status) and status.get("pid") != reclaim_pid:
        return
    paths = daemon_paths(root)
    paths["pid"].unlink(missing_ok=True)
    paths["stop"].unlink(missing_ok=True)


def _acquire_pid_file(root: Path) -> None:
    path = daemon_paths(root)["pid"]
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            with path.open("x", encoding="ascii") as handle:
                handle.write(str(os.getpid()))
            return
        except FileExistsError:
            status = load_daemon_status(root)
            if _has_active_daemon_lock(root, status):
                raise AthenaError(
                    f"Athena daemon is already running with PID {status.get('pid')}"
                ) from None
            _clear_stale_daemon_lock(root)
    raise AthenaError(f"Could not acquire daemon PID file: {path}")


def load_daemon_status(root: Path) -> dict[str, Any]:
    paths = daemon_paths(root)
    status = _read_json(paths["status"])
    try:
        pid = int(paths["pid"].read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        pid = int(status.get("pid", 0) or 0)
    status["pid"] = pid or None
    status["process_alive"] = _pid_running(pid)
    status["process_matches_daemon"] = _pid_is_athena_daemon(pid)
    try:
        heartbeat = datetime.fromisoformat(str(status["heartbeat_at"]))
        status["heartbeat_age_seconds"] = round(
            max(0.0, (datetime.now(UTC) - heartbeat).total_seconds()),
            3,
        )
    except (KeyError, TypeError, ValueError):
        status["heartbeat_age_seconds"] = None
    return status


def load_daemon_diagnostics(root: Path) -> dict[str, Any]:
    return _read_json(daemon_paths(root)["diagnostics"])


def daemon_is_fresh(root: Path, config: AppConfig | None = None) -> bool:
    settings = (config or load_config(root)).daemon
    status = load_daemon_status(root)
    # In-process services used by the CLI/test harness have no PID lock. A persisted lock,
    # however, must be verified so a reused container PID cannot be treated as Athena.
    if daemon_paths(root)["pid"].exists() and not _has_active_daemon_lock(root, status):
        return False
    if not status.get("process_alive") or status.get("state") != "idle":
        return False
    if int(status.get("pending_paths", 0) or 0) != 0:
        return False
    age = status.get("heartbeat_age_seconds")
    if not isinstance(age, (int, float)):
        return False
    return age <= settings.heartbeat_timeout_seconds


class DaemonService:
    def __init__(
        self,
        root: Path,
        runtime: AthenaRuntime | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.root = root.expanduser().resolve()
        self.runtime = runtime or AthenaRuntime(self.root)
        self._owns_runtime = runtime is None
        self.config = self.runtime.config.daemon
        scanner = RepositoryScanner(
            self.root,
            self.runtime.config,
            self.runtime.store,
            self.runtime.analysis_cache,
        )
        # Taking the first snapshot can be expensive on Docker Desktop bind mounts.  The
        # initial scan refreshes it, so defer that walk until after run() publishes status.
        self.watcher = PollingWatcher(scanner.file_snapshot, initialize=False)
        self.coalescer = ChangeCoalescer(
            self.config.debounce_ms / 1000,
            self.config.max_batch_delay_ms / 1000,
        )
        self.monotonic = monotonic
        self.paths = daemon_paths(self.root)
        self.started_at = _utc_now()
        self.scan_count = 0
        self.event_count = 0
        self.last_scan: dict[str, Any] | None = None
        self.last_error: str | None = None
        self._stopping = False
        self._last_status_write = float("-inf")
        self._last_state = ""
        self._retry_at: float | None = None
        self.watcher_backend = (
            "native-watchfiles" if importlib.util.find_spec("watchfiles") is not None else "polling"
        )

    def close(self) -> None:
        if self._owns_runtime:
            self.runtime.close()

    def _write_status(self, state: str, force: bool = False) -> None:
        now = self.monotonic()
        if not force and state == self._last_state and now - self._last_status_write < 1.0:
            return
        _atomic_json(
            self.paths["status"],
            {
                "schema_version": 1,
                "state": state,
                "pid": os.getpid(),
                "root": str(self.root),
                "started_at": self.started_at,
                "heartbeat_at": _utc_now(),
                "poll_interval_ms": self.config.poll_interval_ms,
                "debounce_ms": self.config.debounce_ms,
                "max_batch_delay_ms": self.config.max_batch_delay_ms,
                "watcher_backend": self.watcher_backend,
                "pending_paths": self.coalescer.pending_count,
                "event_count": self.event_count,
                "scan_count": self.scan_count,
                "last_scan": self.last_scan,
                "last_error": self.last_error,
                "diagnostics_path": str(self.paths["diagnostics"]),
            },
        )
        self._last_state = state
        self._last_status_write = now

    def _write_diagnostics(self, warnings: tuple[str, ...], changed: FileChanges) -> None:
        diagnostics = []
        for warning in warnings:
            failed_parse = warning.startswith("Failed to parse ")
            daemon_error = warning.startswith("Daemon scan failed: ")
            path = (
                warning.removeprefix("Failed to parse ").split(":", 1)[0] if failed_parse else None
            )
            diagnostics.append(
                {
                    "severity": "error" if failed_parse or daemon_error else "warning",
                    "code": (
                        "ATHENA_PARSE"
                        if failed_parse
                        else "ATHENA_DAEMON"
                        if daemon_error
                        else "ATHENA_SCAN"
                    ),
                    "message": warning,
                    "source": "athena",
                    **({"path": path} if path else {}),
                }
            )
        _atomic_json(
            self.paths["diagnostics"],
            {
                "schema_version": 1,
                "generated_at": _utc_now(),
                "root": str(self.root),
                "summary": {
                    "errors": sum(item["severity"] == "error" for item in diagnostics),
                    "warnings": sum(item["severity"] == "warning" for item in diagnostics),
                    "changed_paths": changed.count,
                },
                "changed": {
                    "added": sorted(changed.added),
                    "modified": sorted(changed.modified),
                    "deleted": sorted(changed.deleted),
                },
                "diagnostics": diagnostics,
            },
        )

    def _scan(self, changed: FileChanges) -> None:
        try:
            report = self.runtime.scan()
            self.scan_count += 1
            self.last_error = None
            self._retry_at = None
            self.last_scan = {
                "completed_at": _utc_now(),
                "scanned": report.scanned,
                "unchanged": report.unchanged,
                "deleted": report.deleted,
                "chunks": report.chunks,
                "nodes": report.nodes,
                "edges": report.edges,
                "duration_ms": report.duration_ms,
            }
            self._write_diagnostics(report.warnings, changed)
            self.watcher.refresh()
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            self._retry_at = self.monotonic() + max(
                1.0,
                self.config.max_batch_delay_ms / 1000,
            )
            self._write_diagnostics((f"Daemon scan failed: {self.last_error}",), changed)

    def initialize(self) -> None:
        self._scan(FileChanges())
        self._write_status("idle" if self.last_error is None else "degraded", force=True)

    def tick(self, now: float | None = None, observe: bool = True) -> FileChanges | None:
        timestamp = self.monotonic() if now is None else now
        observed = self.watcher.poll() if observe else FileChanges()
        self.event_count += observed.count
        self.coalescer.push(observed, timestamp)
        if self.coalescer.ready(timestamp):
            changes = self.coalescer.flush()
            self._write_status("scanning")
            self._scan(changes)
            self._write_status("idle" if self.last_error is None else "degraded")
            return changes
        if (
            self.last_error is not None
            and self._retry_at is not None
            and timestamp >= self._retry_at
            and self.coalescer.pending_count == 0
        ):
            self._write_status("scanning")
            self._scan(FileChanges())
            self._write_status("idle" if self.last_error is None else "degraded")
            return FileChanges()
        self._write_status("pending" if self.coalescer.pending_count else "idle")
        return None

    def _request_stop(self, *_: object) -> None:
        self._stopping = True

    def _native_filter(self, _change: object, absolute_path: str) -> bool:
        path = Path(absolute_path)
        try:
            relative = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return False
        excluded_prefixes = (
            ".git/",
            ".athena/daemon/",
            ".athena/cache/",
            ".athena/logs/",
            ".mypy_cache/",
            ".pytest_cache/",
            ".ruff_cache/",
            "node_modules/",
            ".venv/",
            "build/",
            "target/",
            "__pycache__/",
        )
        if relative.startswith(excluded_prefixes):
            return False
        return relative == ".gitignore" or path.suffix.casefold() in set(
            self.runtime.config.index.include_extensions
        )

    def _run_native_watcher(self) -> None:
        watchfiles: Any = importlib.import_module("watchfiles")
        try:
            events = watchfiles.watch(
                self.root,
                watch_filter=self._native_filter,
                debounce=50,
                step=50,
                rust_timeout=max(100, self.config.poll_interval_ms),
                yield_on_timeout=True,
            )
            for native_changes in events:
                if self._stopping or self.paths["stop"].exists():
                    break
                if native_changes:
                    self.tick()
                else:
                    self.tick(observe=False)
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            # Read-only bind mounts can contain directories that the native OS watcher cannot
            # subscribe to (for example, an IDE-owned .pytest_cache). Polling uses Athena's
            # already-filtered indexable-file snapshot and remains correct in that case.
            self.watcher_backend = "polling"
            warning = f"Native watcher unavailable; falling back to polling: {type(exc).__name__}: {exc}"
            self._write_diagnostics((warning,), FileChanges())
            self._write_status("idle", force=True)
            if not self._stopping and not self.paths["stop"].exists():
                self._run_polling_watcher()

    def _run_polling_watcher(self) -> None:
        while not self._stopping and not self.paths["stop"].exists():
            self.tick()
            time.sleep(self.config.poll_interval_ms / 1000)

    def run(self) -> None:
        self.paths["directory"].mkdir(parents=True, exist_ok=True)
        existing = load_daemon_status(self.root)
        if _has_active_daemon_lock(self.root, existing) and existing.get("pid") != os.getpid():
            raise AthenaError(f"Athena daemon is already running with PID {existing['pid']}")
        # Container runtimes commonly reuse the same low PID after recreation.  At this
        # point this process has not acquired the lock yet, so a persisted lock bearing our
        # new PID necessarily belongs to the previous container instance.
        _clear_stale_daemon_lock(self.root, reclaim_pid=os.getpid())
        self.paths["stop"].unlink(missing_ok=True)
        _acquire_pid_file(self.root)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._request_stop)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, self._request_stop)
        try:
            # Initial indexing can take minutes on a large repository.  Publish
            # a new record before it starts so callers never mistake the
            # previous container's persisted status for this daemon.
            self._write_status("scanning", force=True)
            self.initialize()
            if self.watcher_backend == "native-watchfiles":
                self._run_native_watcher()
            else:
                self._run_polling_watcher()
        finally:
            try:
                self._write_status("stopped", force=True)
            finally:
                self.paths["pid"].unlink(missing_ok=True)
                self.paths["stop"].unlink(missing_ok=True)
                self.close()


def start_daemon_process(root: Path) -> int:
    resolved = root.expanduser().resolve()
    current = load_daemon_status(resolved)
    if _has_active_daemon_lock(resolved, current):
        raise AthenaError(f"Athena daemon is already running with PID {current['pid']}")
    _clear_stale_daemon_lock(resolved)
    paths = daemon_paths(resolved)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    log = paths["log"].open("a", encoding="utf-8")
    kwargs: dict[str, Any] = {
        "cwd": str(resolved),
        "stdin": subprocess.DEVNULL,
        "stdout": log,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "athena.cli",
                "daemon",
                "run",
                "--root",
                str(resolved),
            ],
            **kwargs,
        )
    finally:
        log.close()
    return process.pid


def ensure_daemon_running(root: Path, wait_seconds: float = 5.0) -> dict[str, Any]:
    resolved = root.expanduser().resolve()
    status = load_daemon_status(resolved)
    if _has_active_daemon_lock(resolved, status):
        return status
    _clear_stale_daemon_lock(resolved)
    pid = start_daemon_process(resolved)
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        status = load_daemon_status(resolved)
        if status.get("process_alive") and status.get("state") in {
            "idle",
            "pending",
            "scanning",
            "degraded",
        }:
            return status
        time.sleep(0.05)
    return {"pid": pid, "process_alive": _pid_running(pid), "state": "starting"}


def request_daemon_stop(root: Path) -> bool:
    resolved = root.expanduser().resolve()
    status = load_daemon_status(resolved)
    if not status.get("process_alive"):
        return False
    stop = daemon_paths(resolved)["stop"]
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.touch()
    return True
