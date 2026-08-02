from __future__ import annotations

import json
from pathlib import Path

import pytest

from athena.errors import EvaluationError
from athena.evaluation import (
    EvaluationThresholds,
    evaluate_gates,
    evaluation_schema,
    load_cases,
    load_dataset,
    run_benchmark,
    run_evaluation,
)
from athena.graph import export_graph
from athena.integrations import generate_adapters
from athena.orchestrator import AthenaRuntime


def _project(root: Path) -> None:
    source = root / "src/main/java/com/acme"
    tests = root / "src/test/java/com/acme"
    source.mkdir(parents=True)
    tests.mkdir(parents=True)
    (source / "BillingService.java").write_text(
        """package com.acme;
import org.springframework.stereotype.Service;
@Service
public class BillingService {
  public String bill() { return "ok"; }
}
""",
        encoding="utf-8",
    )
    (tests / "BillingServiceTest.java").write_text(
        "package com.acme;\nclass BillingServiceTest {}\n", encoding="utf-8"
    )


def test_evaluation_export_and_adapter_generation(tmp_path: Path) -> None:
    _project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        json_path = export_graph(runtime.store, tmp_path / "graph.json", "json")
        graphml_path = export_graph(runtime.store, tmp_path / "graph.graphml", "graphml")
        mermaid_path = export_graph(runtime.store, tmp_path / "graph.mmd", "mermaid")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert any(node["kind"] == "persona" for node in payload["nodes"])
    assert "<graphml" in graphml_path.read_text(encoding="utf-8")
    assert mermaid_path.read_text(encoding="utf-8").startswith("graph TD")

    dataset = tmp_path / "eval.yaml"
    dataset.write_text(
        """cases:
  - id: billing
    query: Add validation to BillingService
    expected_persona: developer
    expected_files: [BillingService.java]
""",
        encoding="utf-8",
    )
    report = run_evaluation(tmp_path, load_cases(dataset))
    assert report["summary"]["routing_accuracy"] == 1.0
    assert report["summary"]["file_recall"] == 1.0

    generated = generate_adapters(tmp_path / "adapters")
    assert len(generated) == 6
    assert all(path.exists() for path in generated)


def test_versioned_benchmark_schema_quality_latency_and_gates(tmp_path: Path) -> None:
    _project(tmp_path)
    dataset_path = tmp_path / "benchmark.yaml"
    dataset_path.write_text(
        """schema_version: 1
name: billing-fixture
benchmark:
  warmup: 0
  iterations: 2
thresholds:
  routing_accuracy_min: 1.0
  file_recall_min: 1.0
  symbol_recall_min: 1.0
  context_type_recall_min: 1.0
  forbidden_hits_max: 0
  context_warm_p95_ms_max: 1000
cases:
  - id: billing
    query: Update BillingService and BillingServiceTest
    expected_persona: developer
    expected_files: [BillingService.java, BillingServiceTest.java]
    expected_symbols: [BillingService]
    expected_context_types: [source, test]
    forbidden_files: [NeverReturn.java]
""",
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)
    report = run_benchmark(tmp_path, dataset, scan=True)

    assert report["schema_version"] == 1
    assert report["summary"]["routing_accuracy"] == 1.0
    assert report["summary"]["file_recall"] == 1.0
    assert report["summary"]["symbol_recall"] == 1.0
    assert report["summary"]["context_type_recall"] == 1.0
    assert report["latency"]["context_cold"]["samples"] == 1
    assert report["latency"]["context_warm"]["samples"] == 2
    assert report["latency"]["exact_lookup_warm"]["p95_ms"] >= 0.0
    assert report["gate"]["passed"] is True
    assert "properties" in evaluation_schema()

    failed = evaluate_gates(report, EvaluationThresholds(context_warm_p95_ms_max=0.000001))
    assert failed["passed"] is False
    assert failed["failures"] == ["context_warm_p95_ms"]


def test_evaluation_schema_rejects_unknown_version_and_context_type(tmp_path: Path) -> None:
    invalid_version = tmp_path / "version.yaml"
    invalid_version.write_text(
        "schema_version: 2\ncases:\n  - id: one\n    query: test\n", encoding="utf-8"
    )
    with pytest.raises(EvaluationError, match="Invalid evaluation dataset"):
        load_dataset(invalid_version)

    invalid_type = tmp_path / "type.yaml"
    invalid_type.write_text(
        """schema_version: 1
cases:
  - id: one
    query: test
    expected_context_types: [unknown]
""",
        encoding="utf-8",
    )
    with pytest.raises(EvaluationError, match="Unsupported expected_context_types"):
        load_dataset(invalid_type)
