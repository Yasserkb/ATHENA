from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from athena import git_sync
from athena.errors import AthenaError
from athena.git_sync import sync_repository


def test_sync_pulls_before_push_and_verifies_upstream(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(root: Path, args: tuple[str, ...]) -> str:
        assert root == tmp_path.resolve()
        calls.append(args)
        responses = {
            ("rev-parse", "--is-inside-work-tree"): "true",
            ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"): "origin/main",
            ("pull", "--rebase", "--autostash"): "Already up to date.",
            ("push",): "",
            ("rev-list", "--left-right", "--count", "HEAD...@{upstream}"): "0\t0",
        }
        return responses[args]

    result = sync_repository(tmp_path, runner)

    assert result.upstream == "origin/main"
    assert calls[-3:] == [
        ("pull", "--rebase", "--autostash"),
        ("push",),
        ("rev-list", "--left-right", "--count", "HEAD...@{upstream}"),
    ]


def test_sync_stops_when_pull_fails(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(_root: Path, args: tuple[str, ...]) -> str:
        calls.append(args)
        if args == ("rev-parse", "--is-inside-work-tree"):
            return "true"
        if args[0] == "rev-parse":
            return "origin/main"
        raise AthenaError("pull conflict")

    with pytest.raises(AthenaError, match="pull conflict"):
        sync_repository(tmp_path, runner)

    assert ("push",) not in calls


def test_sync_rejects_remaining_divergence(tmp_path: Path) -> None:
    def runner(_root: Path, args: tuple[str, ...]) -> str:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return "true"
        if args[0] == "rev-parse":
            return "origin/main"
        if args[0] == "rev-list":
            return "0 1"
        return ""

    with pytest.raises(AthenaError, match=r"still differ.*behind 1"):
        sync_repository(tmp_path, runner)


def test_sync_requires_a_git_worktree(tmp_path: Path) -> None:
    with pytest.raises(AthenaError, match="Not a Git working tree"):
        sync_repository(tmp_path, lambda _root, _args: "false")


def test_sync_requires_an_upstream(tmp_path: Path) -> None:
    def runner(_root: Path, args: tuple[str, ...]) -> str:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return "true"
        raise AthenaError("no upstream configured")

    with pytest.raises(AthenaError, match="current branch has no upstream"):
        sync_repository(tmp_path, runner)


@pytest.mark.parametrize("divergence", ["invalid", "zero one"])
def test_sync_rejects_invalid_divergence_output(tmp_path: Path, divergence: str) -> None:
    def runner(_root: Path, args: tuple[str, ...]) -> str:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return "true"
        if args[0] == "rev-parse":
            return "origin/main"
        if args[0] == "rev-list":
            return divergence
        return ""

    with pytest.raises(AthenaError, match="invalid synchronization status"):
        sync_repository(tmp_path, runner)


def test_git_runner_reports_missing_git(tmp_path: Path, monkeypatch) -> None:
    def missing(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        raise FileNotFoundError

    monkeypatch.setattr(git_sync.subprocess, "run", missing)
    with pytest.raises(AthenaError, match="Git is not installed"):
        git_sync._run_git(tmp_path, ("status",))


def test_git_runner_reports_timeout_and_command_failure(tmp_path: Path, monkeypatch) -> None:
    def timeout(*_args: object, **_kwargs: object) -> CompletedProcess[str]:
        raise TimeoutExpired("git", 120)

    monkeypatch.setattr(git_sync.subprocess, "run", timeout)
    with pytest.raises(AthenaError, match="timed out"):
        git_sync._run_git(tmp_path, ("pull",))

    monkeypatch.setattr(
        git_sync.subprocess,
        "run",
        lambda *_args, **_kwargs: CompletedProcess(
            ["git", "push"], 1, stdout="", stderr="rejected"
        ),
    )
    with pytest.raises(AthenaError, match="git push failed: rejected"):
        git_sync._run_git(tmp_path, ("push",))
