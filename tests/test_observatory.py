from __future__ import annotations

import json
from pathlib import Path

from athena.observatory import ObservatoryService, ProjectRegistry
from athena.orchestrator import AthenaRuntime


def _indexed_project(root: Path) -> None:
    source = root / "src" / "billing.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "class BillingService:\n"
        "    def invoice(self, customer_id: str) -> str:\n"
        "        return customer_id\n\n"
        + "\n".join(f"# billing domain note {index}" for index in range(1500)),
        encoding="utf-8",
    )
    with AthenaRuntime(root) as runtime:
        runtime.scan()
        bundle = runtime.context("Update BillingService invoice", "developer")
        assert bundle.hits


def test_project_registry_round_trip_and_remove(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ATHENA_STATE_DIR", raising=False)
    root = tmp_path / "project"
    root.mkdir()
    registry = ProjectRegistry(tmp_path / "observatory.json")

    first = registry.add(root)
    second = registry.add(root)

    assert first.project_id == second.project_id
    assert registry.get(first.project_id) == second
    assert len(registry.all()) == 1
    payload = json.loads(registry.path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert registry.remove(first.project_id) is True
    assert registry.remove(first.project_id) is False


def test_observatory_reports_health_savings_and_retrieval_graph(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("ATHENA_STATE_DIR", raising=False)
    root = tmp_path / "billing"
    root.mkdir()
    _indexed_project(root)
    registry = ProjectRegistry(tmp_path / "registry.json")
    entry = registry.add(root)
    service = ObservatoryService(registry)

    overview = service.overview()
    detail = service.project(entry.project_id)

    assert overview["summary"]["projects"] == 1
    assert overview["summary"]["context_requests"] == 1
    assert overview["summary"]["tokens_avoided"] > 0
    assert detail["stats"]["files"] >= 1
    assert detail["savings"]["baseline"] == "full-index-per-context-request"
    assert detail["latest_context"]["selected_evidence"]
    assert detail["retrieval_graph"]["nodes"]
    assert detail["graph"]["nodes"]


def test_uninitialized_project_is_visible_without_creating_an_index(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("ATHENA_STATE_DIR", raising=False)
    root = tmp_path / "empty"
    root.mkdir()
    registry = ProjectRegistry(tmp_path / "registry.json")
    entry = registry.add(root)

    project = ObservatoryService(registry).project(entry.project_id)

    assert project["health"] == "uninitialized"
    assert project["initialized"] is False
    assert not entry.database.exists()
