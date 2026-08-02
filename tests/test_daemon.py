from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from athena.daemon import (
    ChangeCoalescer,
    DaemonService,
    FileChanges,
    PollingWatcher,
    daemon_is_fresh,
    daemon_paths,
    ensure_daemon_running,
    load_daemon_diagnostics,
    load_daemon_status,
)
from athena.daemon import service as daemon_service
from athena.orchestrator import AthenaRuntime


def test_polling_watcher_reports_added_modified_and_deleted_paths() -> None:
    state = {"A.java": (1, 1), "deleted.py": (2, 1)}
    watcher = PollingWatcher(lambda: dict(state))

    state["A.java"] = (3, 2)
    state["B.ts"] = (4, 1)
    del state["deleted.py"]
    changes = watcher.poll()

    assert changes.added == frozenset({"B.ts"})
    assert changes.modified == frozenset({"A.java"})
    assert changes.deleted == frozenset({"deleted.py"})


def test_polling_watcher_can_defer_expensive_initial_snapshot() -> None:
    calls = 0

    def snapshot() -> dict[str, tuple[int, int]]:
        nonlocal calls
        calls += 1
        return {"app.py": (1, 1)}

    watcher = PollingWatcher(snapshot, initialize=False)
    assert calls == 0
    watcher.refresh()
    assert calls == 1


@pytest.mark.parametrize(
    "arguments",
    [
        ["python", "-m", "athena.cli", "daemon", "run", "--root", "/workspace"],
        ["/opt/venv/bin/python", "/opt/venv/bin/athena", "daemon", "run"],
    ],
)
def test_daemon_process_arguments_recognize_module_and_console_entrypoints(
    arguments: list[str],
) -> None:
    assert daemon_service._arguments_are_athena_daemon(arguments)


def test_change_coalescer_debounces_and_preserves_final_path_state() -> None:
    coalescer = ChangeCoalescer(debounce_seconds=0.5, max_delay_seconds=2.0)
    coalescer.push(FileChanges(added=frozenset({"A.java"})), now=0.0)
    coalescer.push(
        FileChanges(
            modified=frozenset({"A.java", "B.py"}),
            deleted=frozenset({"gone.ts"}),
        ),
        now=0.2,
    )

    assert not coalescer.ready(0.6)
    assert coalescer.ready(0.71)
    changes = coalescer.flush()
    assert changes.added == frozenset({"A.java"})
    assert changes.modified == frozenset({"B.py"})
    assert changes.deleted == frozenset({"gone.ts"})
    assert coalescer.pending_count == 0


def test_change_coalescer_flushes_continuous_changes_at_max_delay() -> None:
    coalescer = ChangeCoalescer(debounce_seconds=1.0, max_delay_seconds=2.0)
    coalescer.push(FileChanges(modified=frozenset({"A.java"})), now=0.0)
    coalescer.push(FileChanges(modified=frozenset({"B.java"})), now=1.5)
    assert coalescer.ready(2.0)


def test_daemon_incrementally_scans_after_debounce_and_writes_diagnostics(
    tmp_path: Path,
) -> None:
    source = tmp_path / "Service.java"
    source.write_text("class Service {}\n", encoding="utf-8")
    clock = [0.0]

    with AthenaRuntime(tmp_path) as runtime:
        runtime.config.daemon.debounce_ms = 100
        runtime.config.daemon.max_batch_delay_ms = 500
        service = DaemonService(tmp_path, runtime=runtime, monotonic=lambda: clock[0])
        service.initialize()
        assert service.scan_count == 1
        assert daemon_is_fresh(tmp_path, runtime.config)

        source.write_text("class Service { void changed() {} }\n", encoding="utf-8")
        clock[0] = 0.01
        assert service.tick() is None
        assert load_daemon_status(tmp_path)["state"] == "pending"

        clock[0] = 0.12
        flushed = service.tick()
        assert flushed is not None
        assert flushed.modified == frozenset({"Service.java"})
        assert service.scan_count == 2
        assert runtime.store.exact_nodes("changed")

    diagnostics = load_daemon_diagnostics(tmp_path)
    assert diagnostics["schema_version"] == 1
    assert diagnostics["summary"]["changed_paths"] == 1
    assert diagnostics["diagnostics"] == []


def test_daemon_runtime_files_do_not_trigger_watcher(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    with AthenaRuntime(tmp_path) as runtime:
        service = DaemonService(tmp_path, runtime=runtime)
        service.initialize()
        status = load_daemon_status(tmp_path)
        assert status["state"] == "idle"
        assert service.watcher.poll().count == 0
        assert (
            json.loads(
                (tmp_path / ".athena" / "daemon" / "status.json").read_text(encoding="utf-8")
            )["scan_count"]
            == 1
        )


def test_native_watcher_failure_falls_back_to_polling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    with AthenaRuntime(tmp_path) as runtime:
        service = DaemonService(tmp_path, runtime=runtime)
        service.initialize()
        service.watcher_backend = "native-watchfiles"
        polling_started: list[bool] = []

        class NativeWatcherFailure(BaseException):
            pass

        def fail_watch(*_args: object, **_kwargs: object) -> object:
            raise NativeWatcherFailure("permission denied")

        monkeypatch.setattr(
            daemon_service.importlib,
            "import_module",
            lambda _name: SimpleNamespace(watch=fail_watch),
        )
        monkeypatch.setattr(service, "_run_polling_watcher", lambda: polling_started.append(True))

        service._run_native_watcher()

    assert service.watcher_backend == "polling"
    assert polling_started == [True]
    diagnostics = load_daemon_diagnostics(tmp_path)
    assert "falling back to polling" in diagnostics["diagnostics"][0]["message"]


def test_ensure_daemon_reclaims_stopped_pid_reused_by_container_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = daemon_paths(tmp_path)
    paths["directory"].mkdir(parents=True)
    paths["pid"].write_text("8", encoding="ascii")
    paths["stop"].touch()
    paths["status"].write_text(
        json.dumps({"state": "stopped", "pid": 8, "heartbeat_at": "2020-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(daemon_service, "_pid_running", lambda _pid: True)
    started: list[Path] = []

    def start(root: Path) -> int:
        started.append(root)
        assert not paths["pid"].exists()
        assert not paths["stop"].exists()
        paths["status"].write_text(
            json.dumps({"state": "idle", "pid": 9, "heartbeat_at": "2026-01-01T00:00:00+00:00"}),
            encoding="utf-8",
        )
        return 9

    monkeypatch.setattr(daemon_service, "start_daemon_process", start)

    status = ensure_daemon_running(tmp_path, wait_seconds=0.1)

    assert started == [tmp_path.resolve()]
    assert status["pid"] == 9
    assert status["state"] == "idle"


def test_daemon_freshness_rejects_reused_pid_with_active_looking_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = daemon_paths(tmp_path)
    paths["directory"].mkdir(parents=True)
    paths["pid"].write_text("8", encoding="ascii")
    paths["status"].write_text(
        json.dumps({"state": "idle", "pid": 8, "heartbeat_at": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(daemon_service, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(daemon_service, "_pid_is_athena_daemon", lambda _pid: False)

    assert not daemon_is_fresh(tmp_path)


def test_foreground_daemon_reclaims_same_pid_from_previous_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = daemon_paths(tmp_path)
    paths["directory"].mkdir(parents=True)
    paths["pid"].write_text("7", encoding="ascii")
    paths["status"].write_text(
        json.dumps({"state": "scanning", "pid": 7, "heartbeat_at": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(daemon_service, "_pid_is_athena_daemon", lambda _pid: True)

    daemon_service._clear_stale_daemon_lock(tmp_path, reclaim_pid=7)

    assert not paths["pid"].exists()


def test_daemon_reports_scan_failure_and_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    clock = [0.0]
    with AthenaRuntime(tmp_path) as runtime:
        original_scan = runtime.scan
        attempts = [0]

        def flaky_scan() -> object:
            attempts[0] += 1
            if attempts[0] == 1:
                raise RuntimeError("temporary failure")
            return original_scan()

        monkeypatch.setattr(runtime, "scan", flaky_scan)
        service = DaemonService(tmp_path, runtime=runtime, monotonic=lambda: clock[0])
        service.initialize()
        failed = load_daemon_diagnostics(tmp_path)
        assert failed["summary"]["errors"] == 1
        assert failed["diagnostics"][0]["code"] == "ATHENA_DAEMON"
        assert load_daemon_status(tmp_path)["state"] == "degraded"

        clock[0] = 3.0
        retried = service.tick(observe=False)
        assert retried == FileChanges()
        assert attempts[0] == 2
        assert service.last_error is None
        assert load_daemon_status(tmp_path)["state"] == "idle"
