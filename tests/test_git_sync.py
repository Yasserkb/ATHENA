from pathlib import Path

import pytest

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
