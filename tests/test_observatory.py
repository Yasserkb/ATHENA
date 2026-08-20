from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path

from athena.observatory import ObservatoryService, ProjectRegistry
from athena.observatory.server import ObservatoryHTTPServer, _handler
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


@contextmanager
def _running_observatory(service: ObservatoryService) -> Iterator[tuple[str, int]]:
    server: HTTPServer = ObservatoryHTTPServer(("127.0.0.1", 0), _handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield str(host), int(port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


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


def test_observatory_http_health_static_headers_and_not_found(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    service = ObservatoryService(ProjectRegistry(tmp_path / "registry.json"))
    service.register(root)

    with _running_observatory(service) as (host, port):
        connection = HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/api/health")
        health = connection.getresponse()
        assert health.status == 200
        assert json.loads(health.read()) == {"status": "ok"}
        assert health.getheader("X-Content-Type-Options") == "nosniff"

        connection.request("GET", "/missing")
        missing = connection.getresponse()
        assert missing.status == 404
        missing.read()
        connection.close()


def test_observatory_http_rejects_untrusted_host_and_cross_origin_mutation(
    tmp_path: Path,
) -> None:
    service = ObservatoryService(ProjectRegistry(tmp_path / "registry.json"))

    with _running_observatory(service) as (host, port):
        connection = HTTPConnection(host, port, timeout=2)
        connection.putrequest("GET", "/api/health", skip_host=True)
        connection.putheader("Host", "attacker.example")
        connection.endheaders()
        untrusted = connection.getresponse()
        assert untrusted.status == 403
        untrusted.read()

        body = json.dumps({"root": str(tmp_path)}).encode()
        connection.request(
            "POST",
            "/api/projects",
            body=body,
            headers={"Content-Type": "application/json", "Origin": "https://attacker.example"},
        )
        cross_origin = connection.getresponse()
        assert cross_origin.status == 403
        cross_origin.read()
        connection.close()


def test_observatory_http_registers_reads_and_removes_project(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    service = ObservatoryService(ProjectRegistry(tmp_path / "registry.json"))

    with _running_observatory(service) as (host, port):
        connection = HTTPConnection(host, port, timeout=2)
        body = json.dumps({"root": str(root)}).encode()
        connection.request(
            "POST",
            "/api/projects",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        created = connection.getresponse()
        assert created.status == 201
        project = json.loads(created.read())

        connection.request("GET", f"/api/projects/{project['id']}")
        detail = connection.getresponse()
        assert detail.status == 200
        assert json.loads(detail.read())["root"] == str(root.resolve())

        connection.request("DELETE", f"/api/projects/{project['id']}")
        removed = connection.getresponse()
        assert removed.status == 200
        removed.read()
        connection.close()
