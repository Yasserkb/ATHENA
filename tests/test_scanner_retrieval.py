import subprocess
from pathlib import Path

from athena.orchestrator import AthenaRuntime


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_git_project(root: Path) -> None:
    (root / ".gitignore").write_text(".athena/index.db*\n", encoding="utf-8")
    _git(root, "init")
    _git(root, "config", "user.email", "athena@example.test")
    _git(root, "config", "user.name", "Athena Tests")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "initial")


def _write_project(root: Path) -> None:
    (root / "src/main/java/com/acme").mkdir(parents=True)
    (root / "src/test/java/com/acme").mkdir(parents=True)
    (root / "src/main/resources").mkdir(parents=True)
    (root / "src/main/java/com/acme/OrderController.java").write_text(
        """package com.acme;
import org.springframework.web.bind.annotation.RestController;
@RestController
public class OrderController {
  private final OrderService orderService;
  public OrderController(OrderService orderService) { this.orderService = orderService; }
  public String create() { return orderService.create(); }
}
""",
        encoding="utf-8",
    )
    (root / "src/main/java/com/acme/OrderService.java").write_text(
        """package com.acme;
import org.springframework.stereotype.Service;
@Service
public class OrderService {
  private final OrderRepository orderRepository;
  public OrderService(OrderRepository orderRepository) { this.orderRepository = orderRepository; }
  public String create() { return orderRepository.save(); }
}
""",
        encoding="utf-8",
    )
    (root / "src/main/java/com/acme/OrderRepository.java").write_text(
        """package com.acme;
import org.springframework.stereotype.Repository;
@Repository
public interface OrderRepository { String save(); }
""",
        encoding="utf-8",
    )
    (root / "src/test/java/com/acme/OrderServiceTest.java").write_text(
        """package com.acme;
class OrderServiceTest { void createsOrder() {} }
""",
        encoding="utf-8",
    )
    (root / "src/main/resources/application.yml").write_text(
        "order:\n  timeout-ms: ${ORDER_TIMEOUT:1000}\n", encoding="utf-8"
    )


def test_incremental_scan_and_context(tmp_path: Path) -> None:
    _write_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        first = runtime.scan()
        assert first.scanned == 5
        assert runtime.store.stats()["chunks"] >= 5
        second = runtime.scan()
        assert second.scanned == 0
        assert second.unchanged == 5
        bundle = runtime.context("Add validation to OrderService create", "developer")
        assert bundle.hits
        assert any("OrderService.java" in hit.chunk.path for hit in bundle.hits)
        assert bundle.estimated_tokens <= bundle.persona.policy.max_context_tokens
        graph = runtime.graph("OrderController")
        assert any(row["relation"] in {"RESOLVED_DEPENDS_ON", "FOLLOWS_PATTERN"} for row in graph)


def test_metadata_avoids_reading_unchanged_content(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        from athena.indexing.scanner import RepositoryScanner

        original = Path.read_bytes

        def fail_if_read(path: Path) -> bytes:
            raise AssertionError(f"unchanged source content was read: {path}")

        monkeypatch.setattr(Path, "read_bytes", fail_if_read)
        try:
            report = RepositoryScanner(tmp_path, runtime.config, runtime.store).scan()
        finally:
            monkeypatch.setattr(Path, "read_bytes", original)
        assert report.scanned == 0
        assert report.unchanged == 5


def test_git_discovers_dirty_untracked_deleted_and_renamed_files(tmp_path: Path) -> None:
    _write_project(tmp_path)
    _init_git_project(tmp_path)
    service = tmp_path / "src/main/java/com/acme/OrderService.java"
    repository = tmp_path / "src/main/java/com/acme/OrderRepository.java"
    controller = tmp_path / "src/main/java/com/acme/OrderController.java"
    renamed = controller.with_name("ApiController.java")
    added = service.with_name("AuditService.java")

    with AthenaRuntime(tmp_path) as runtime:
        assert runtime.scan().scanned == 5
        clean = runtime.scan()
        assert clean.scanned == 0
        assert clean.unchanged == 5

        service.write_text(service.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")
        added.write_text("package com.acme;\nclass AuditService {}\n", encoding="utf-8")
        repository.unlink()
        controller.rename(renamed)

        changed = runtime.scan()
        assert changed.scanned == 3
        assert changed.deleted == 2
        indexed = runtime.store.indexed_paths()
        assert "src/main/java/com/acme/AuditService.java" in indexed
        assert "src/main/java/com/acme/ApiController.java" in indexed
        assert "src/main/java/com/acme/OrderController.java" not in indexed
        assert "src/main/java/com/acme/OrderRepository.java" not in indexed


def test_git_commit_diff_scans_only_committed_paths(tmp_path: Path) -> None:
    _write_project(tmp_path)
    _init_git_project(tmp_path)
    service = tmp_path / "src/main/java/com/acme/OrderService.java"
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        service.write_text(
            service.read_text(encoding="utf-8") + "\n// committed\n", encoding="utf-8"
        )
        _git(tmp_path, "add", str(service.relative_to(tmp_path)))
        _git(tmp_path, "commit", "-m", "change service")
        report = runtime.scan()
        assert report.scanned == 1
        assert report.deleted == 0


def test_git_restore_after_dirty_scan_reconciles_previous_index(tmp_path: Path) -> None:
    _write_project(tmp_path)
    _init_git_project(tmp_path)
    service = tmp_path / "src/main/java/com/acme/OrderService.java"
    original = service.read_text(encoding="utf-8")
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        service.write_text(original.replace("OrderService", "DirtyService"), encoding="utf-8")
        assert runtime.scan().scanned == 1
        assert runtime.store.exact_nodes(["DirtyService"])

        _git(tmp_path, "restore", str(service.relative_to(tmp_path)))
        restored = runtime.scan()
        assert restored.scanned == 1
        assert runtime.store.exact_nodes(["OrderService"])
        assert not runtime.store.exact_nodes(["DirtyService"])


def test_parallel_parser_batches_are_reported(tmp_path: Path) -> None:
    _write_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.config.index.parse_workers = 2
        runtime.config.index.write_batch_size = 2
        runtime.scan()
        metrics = runtime.store.metrics_summary(tmp_path.name, 1)
        payload = metrics["recent"][0]["payload"]
        assert payload["workers"] == 2
        assert payload["write_batches"] == 3
        assert payload["failures"] == 0


def test_parser_failure_preserves_previous_file_analysis(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path)
    service = tmp_path / "src/main/java/com/acme/OrderService.java"
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        before = runtime.store.exact_nodes(["OrderService"])[0][0]
        service.write_text(service.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")

        from athena.indexing.parsers.java import JavaParser

        original = JavaParser.analyze

        def fail_service(parser, path: str, text: str, digest: str):
            if path.endswith("OrderService.java"):
                raise ValueError("synthetic parser failure")
            return original(parser, path, text, digest)

        monkeypatch.setattr(JavaParser, "analyze", fail_service)
        report = runtime.scan()
        after = runtime.store.exact_nodes(["OrderService"])[0][0]
        assert after == before
        assert any("synthetic parser failure" in warning for warning in report.warnings)
        assert runtime.store.metadata()["index_degraded"] == "true"
        status = runtime.status()
        assert status["index_degraded"] is True
        assert status["failed_paths"] == ["src/main/java/com/acme/OrderService.java"]


def _derived_snapshot(runtime: AthenaRuntime) -> tuple[set[tuple[str, str, str]], set[str]]:
    edges = {
        (str(edge["source_id"]), str(edge["relation"]), str(edge["target_id"]))
        for edge in runtime.store.all_edges()
        if str(edge["evidence_path"]).startswith("@derived")
    }
    nodes = {
        node.node_id
        for node in runtime.store.all_nodes()
        if node.path and node.path.startswith("@derived")
    }
    return edges, nodes


def test_incremental_derivation_matches_full_rebuild(tmp_path: Path) -> None:
    _write_project(tmp_path)
    _init_git_project(tmp_path)
    service = tmp_path / "src/main/java/com/acme/OrderService.java"
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        service.write_text(service.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")
        incremental_report = runtime.scan()
        incremental = _derived_snapshot(runtime)
        metrics = runtime.store.metrics_summary(tmp_path.name, 1)["recent"][0]["payload"]
        assert metrics["derivation_mode"] == "incremental"
        assert metrics["derived_owners"] < runtime.store.stats()["files"]

        from athena.indexing.patterns import ArchitectureDeriver
        from athena.indexing.scanner import repository_identity

        repository_name, repository_id = repository_identity(tmp_path)
        ArchitectureDeriver().derive(runtime.store, repository_id, repository_name)
        assert _derived_snapshot(runtime) == incremental
        assert incremental_report.scanned == 1


def test_new_symbol_incrementally_resolves_existing_reference(tmp_path: Path) -> None:
    source = tmp_path / "src/main/java/com/acme"
    source.mkdir(parents=True)
    caller = source / "Caller.java"
    caller.write_text(
        """package com.acme;
class Caller {
  private final MissingService missingService;
}
""",
        encoding="utf-8",
    )
    _init_git_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        assert not any(
            edge["relation"] == "RESOLVED_DEPENDS_ON" for edge in runtime.store.all_edges()
        )
        (source / "MissingService.java").write_text(
            "package com.acme;\nclass MissingService {}\n", encoding="utf-8"
        )
        runtime.scan()
        assert any(
            edge["relation"] == "RESOLVED_DEPENDS_ON"
            and edge["source_id"] == "java::com.acme.Caller"
            and edge["target_id"] == "java::com.acme.MissingService"
            for edge in runtime.store.all_edges()
        )


def test_deleted_file_is_removed(tmp_path: Path) -> None:
    _write_project(tmp_path)
    target = tmp_path / "src/main/java/com/acme/OrderRepository.java"
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        target.unlink()
        report = runtime.scan()
        assert report.deleted == 1
        assert not [
            node
            for node, _ in runtime.store.exact_nodes(["OrderRepository"])
            if node.path and node.path.endswith("OrderRepository.java")
        ]


def test_task_terms_do_not_seed_unrelated_persona_policy_nodes(tmp_path: Path) -> None:
    _write_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        bundle = runtime.context("Update OrderService and its related test", "developer")
        assert not any("PERSONA_" in line for line in bundle.architecture)
        assert not any("persona-policy" in line for line in bundle.architecture)


def test_persona_policy_constrains_seeds_and_boosts_matching_tags(tmp_path: Path) -> None:
    _write_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        bundle = runtime.context("Add validation to OrderService create", "developer")
        assert bundle.hits
        assert any("persona-tag:service" in hit.reasons for hit in bundle.hits)


def test_context_uses_full_primary_and_compressed_secondary_evidence(tmp_path: Path) -> None:
    _write_project(tmp_path)
    extra = tmp_path / "src/main/java/com/acme/LongHelper.java"
    extra.write_text(
        "package com.acme;\npublic class LongHelper {\n"
        + "\n".join(f'  String line{index}() {{ return "{index}"; }}' for index in range(60))
        + "\n}\n",
        encoding="utf-8",
    )
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        bundle = runtime.context("Add validation to OrderService and LongHelper", "developer")
        assert bundle.estimated_tokens <= bundle.persona.policy.max_context_tokens
        assert bundle.hits
        assert all(
            "compressed-secondary-evidence" in hit.reasons or hit == bundle.hits[0]
            for hit in bundle.hits
        )


def test_context_bundle_cache_is_invalidated_by_index_generation(tmp_path: Path) -> None:
    source = tmp_path / "CacheService.java"
    source.write_text(
        'class CacheService { String value() { return "oldMarker"; } }\n',
        encoding="utf-8",
    )
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        first = runtime.context("Update CacheService", "developer")
        second = runtime.context("Update CacheService", "developer")
        assert second is first
        assert runtime.status()["caches"]["context_bundles"]["hits"] == 1

        source.write_text(
            'class CacheService { String value() { return "newMarker"; } }\n',
            encoding="utf-8",
        )
        runtime.scan()
        refreshed = runtime.context("Update CacheService", "developer")

        assert refreshed is not first
        evidence = "\n".join(hit.chunk.content for hit in refreshed.hits)
        assert "newMarker" in evidence
        assert "oldMarker" not in evidence
        cache_status = runtime.status()["caches"]["context_bundles"]
        assert cache_status["invalidations"] == 1


def test_parsed_analysis_cache_reuses_restored_content(tmp_path: Path) -> None:
    source = tmp_path / "RestoredService.java"
    original = 'class RestoredService { String state() { return "original"; } }\n'
    source.write_text(original, encoding="utf-8")
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        source.write_text(
            'class RestoredService { String state() { return "changed"; } }\n',
            encoding="utf-8",
        )
        runtime.scan()
        source.write_text(original, encoding="utf-8")
        runtime.scan()

        parsed_cache = runtime.status()["caches"]["parsed_files"]
        assert parsed_cache["hits"] >= 1
        assert runtime.store.exact_nodes(["RestoredService"])


def test_clean_scan_preserves_generation_and_warm_bundle(tmp_path: Path) -> None:
    _write_project(tmp_path)
    _init_git_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        first = runtime.context("Update OrderService", "developer")
        generation = runtime.store.index_generation()

        report = runtime.scan()
        second = runtime.context("Update OrderService", "developer")

        assert report.scanned == 0
        assert runtime.store.index_generation() == generation
        assert second is first
