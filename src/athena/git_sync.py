from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from athena.errors import AthenaError


@dataclass(frozen=True, slots=True)
class GitSyncResult:
    upstream: str
    ahead: int
    behind: int


GitRunner = Callable[[Path, Sequence[str]], str]


def _run_git(root: Path, args: Sequence[str]) -> str:
    try:
        process = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise AthenaError("Git is not installed or is not available on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise AthenaError(f"Git command timed out: git {' '.join(args)}") from exc
    except OSError as exc:
        raise AthenaError(f"Could not run Git: {exc}") from exc
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown Git error"
        raise AthenaError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def sync_repository(root: Path, runner: GitRunner = _run_git) -> GitSyncResult:
    """Rebase from the configured upstream, push, and verify exact synchronization."""
    resolved = root.expanduser().resolve()
    if runner(resolved, ("rev-parse", "--is-inside-work-tree")) != "true":
        raise AthenaError(f"Not a Git working tree: {resolved}")

    try:
        upstream = runner(
            resolved,
            ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"),
        )
    except AthenaError as exc:
        raise AthenaError(
            "The current branch has no upstream; configure one with "
            "'git push --set-upstream <remote> <branch>'"
        ) from exc

    runner(resolved, ("pull", "--rebase", "--autostash"))
    runner(resolved, ("push",))
    divergence = runner(resolved, ("rev-list", "--left-right", "--count", "HEAD...@{upstream}"))
    fields = divergence.replace("\t", " ").split()
    if len(fields) != 2:
        raise AthenaError(f"Git returned an invalid synchronization status: {divergence!r}")
    try:
        ahead, behind = (int(value) for value in fields)
    except ValueError as exc:
        raise AthenaError(f"Git returned an invalid synchronization status: {divergence!r}") from exc
    if ahead or behind:
        raise AthenaError(
            f"Push completed but HEAD and {upstream} still differ "
            f"(ahead {ahead}, behind {behind})"
        )
    return GitSyncResult(upstream, ahead, behind)
