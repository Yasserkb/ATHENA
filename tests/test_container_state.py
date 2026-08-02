from __future__ import annotations

from pathlib import Path

import pytest

from athena.config import AppConfig, database_path, state_directory
from athena.daemon import daemon_paths
from athena.errors import ConfigurationError
from athena.orchestrator import AthenaRuntime


def test_external_state_directory_separates_runtime_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    state = tmp_path / "state"
    repository.mkdir()
    (repository / "Service.py").write_text("class Service:\n    pass\n", encoding="utf-8")
    monkeypatch.setenv("ATHENA_STATE_DIR", str(state))

    assert state_directory() == state.resolve()
    assert database_path(repository, AppConfig()) == state.resolve() / "index.db"
    assert daemon_paths(repository)["directory"] == state.resolve() / "daemon"

    with AthenaRuntime(repository) as runtime:
        runtime.scan()
        assert runtime.store.path == state.resolve() / "index.db"

    assert (state / "index.db").is_file()
    assert not (repository / ".athena" / "index.db").exists()


def test_external_state_directory_must_be_absolute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATHENA_STATE_DIR", "relative-state")
    with pytest.raises(ConfigurationError, match="absolute"):
        state_directory()
