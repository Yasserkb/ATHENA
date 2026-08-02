from __future__ import annotations

import json
import math
import platform
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from statistics import mean
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from athena import __version__
from athena.application import ContextCompiler
from athena.domain import ContextBundle
from athena.errors import EvaluationError
from athena.indexing.common import exact_search_terms
from athena.orchestrator import AthenaRuntime
from athena.storage import SQLiteStore

_CONTEXT_TYPES = {"source", "test", "configuration", "database", "documentation"}


class BenchmarkSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warmup: int = Field(default=1, ge=0, le=20)
    iterations: int = Field(default=5, ge=1, le=100)


class EvaluationThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routing_accuracy_min: float | None = Field(default=None, ge=0.0, le=1.0)
    file_precision_min: float | None = Field(default=None, ge=0.0, le=1.0)
    file_recall_min: float | None = Field(default=None, ge=0.0, le=1.0)
    symbol_recall_min: float | None = Field(default=None, ge=0.0, le=1.0)
    context_type_recall_min: float | None = Field(default=None, ge=0.0, le=1.0)
    mrr_min: float | None = Field(default=None, ge=0.0, le=1.0)
    forbidden_hits_max: int | None = Field(default=None, ge=0)
    max_estimated_tokens: int | None = Field(default=None, ge=1)
    exact_p95_ms_max: float | None = Field(default=None, gt=0)
    fts_p95_ms_max: float | None = Field(default=None, gt=0)
    graph_p95_ms_max: float | None = Field(default=None, gt=0)
    context_cold_p95_ms_max: float | None = Field(default=None, gt=0)
    context_warm_p95_ms_max: float | None = Field(default=None, gt=0)
    no_change_scan_p95_ms_max: float | None = Field(default=None, gt=0)


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    query: str
    expected_persona: str | None = None
    expected_files: tuple[str, ...] = ()
    forbidden_files: tuple[str, ...] = ()
    expected_symbols: tuple[str, ...] = ()
    expected_context_types: tuple[str, ...] = ()
    profile: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationDataset:
    schema_version: int
    name: str
    cases: tuple[EvalCase, ...]
    benchmark: BenchmarkSettings
    thresholds: EvaluationThresholds


@dataclass(frozen=True, slots=True)
class EvalResult:
    case_id: str
    persona: str
    route_correct: bool | None
    precision: float | None
    recall: float | None
    symbol_recall: float | None
    context_type_recall: float | None
    reciprocal_rank: float | None
    forbidden_hits: int
    latency_ms: float
    estimated_tokens: int
    retrieved_files: tuple[str, ...] = field(default_factory=tuple)
    retrieved_symbols: tuple[str, ...] = field(default_factory=tuple)
    context_types: tuple[str, ...] = field(default_factory=tuple)


class _CaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str | None = Field(default=None, validation_alias=AliasChoices("id", "case_id"))
    query: str = Field(min_length=1)
    expected_persona: str | None = Field(
        default=None, validation_alias=AliasChoices("expected_persona", "persona")
    )
    expected_files: list[str] = Field(default_factory=list)
    expected_symbols: list[str] = Field(default_factory=list)
    expected_context_types: list[str] = Field(default_factory=list)
    forbidden_files: list[str] = Field(default_factory=list)
    profile: Literal["economy", "copilot-economy", "eco", "balanced", "deep", "auto"] | None = None

    def to_domain(self, fallback_id: str) -> EvalCase:
        invalid_types = set(self.expected_context_types) - _CONTEXT_TYPES
        if invalid_types:
            raise ValueError(
                "Unsupported expected_context_types: " + ", ".join(sorted(invalid_types))
            )
        return EvalCase(
            self.case_id or fallback_id,
            self.query,
            self.expected_persona,
            tuple(self.expected_files),
            tuple(self.forbidden_files),
            tuple(self.expected_symbols),
            tuple(self.expected_context_types),
            self.profile,
        )


class _DatasetModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    name: str = "athena-evaluation"
    cases: list[_CaseModel] = Field(min_length=1)
    benchmark: BenchmarkSettings = Field(default_factory=BenchmarkSettings)
    thresholds: EvaluationThresholds = Field(default_factory=EvaluationThresholds)


def evaluation_schema() -> dict[str, Any]:
    return _DatasetModel.model_json_schema()


def load_dataset(path: Path) -> EvaluationDataset:
    try:
        raw = path.read_text(encoding="utf-8")
        data: Any = (
            yaml.safe_load(raw) if path.suffix.casefold() in {".yaml", ".yml"} else json.loads(raw)
        )
        if isinstance(data, list):
            data = {"schema_version": 1, "cases": data}
        model = _DatasetModel.model_validate(data)
        cases = tuple(case.to_domain(str(index)) for index, case in enumerate(model.cases, 1))
    except (OSError, json.JSONDecodeError, yaml.YAMLError, ValidationError, ValueError) as exc:
        raise EvaluationError(f"Invalid evaluation dataset {path}: {exc}") from exc
    return EvaluationDataset(
        model.schema_version, model.name, cases, model.benchmark, model.thresholds
    )


def load_cases(path: Path) -> list[EvalCase]:
    return list(load_dataset(path).cases)


def run_evaluation(root: Path, cases: Sequence[EvalCase]) -> dict[str, Any]:
    results: list[EvalResult] = []
    with AthenaRuntime(root) as runtime:
        for case in cases:
            started = time.perf_counter()
            bundle = runtime.context(case.query, profile=case.profile)
            latency_ms = (time.perf_counter() - started) * 1000
            results.append(_evaluate_bundle(case, bundle, latency_ms, runtime.store))
    return _quality_report(results)


def run_benchmark(
    root: Path,
    dataset: EvaluationDataset,
    *,
    scan: bool = False,
    mode: Literal["full", "economy"] = "full",
) -> dict[str, Any]:
    results: list[EvalResult] = []
    latency: dict[str, list[float]] = {
        "context_cold": [],
        "context_warm": [],
        "exact_lookup_cold": [],
        "exact_lookup_warm": [],
        "fts_cold": [],
        "fts_warm": [],
        "graph_walk_cold": [],
        "graph_walk_warm": [],
        "no_change_scan": [],
    }
    settings = dataset.benchmark
    with AthenaRuntime(root) as runtime:
        if scan:
            runtime.scan()
        if runtime.store.stats()["files"] == 0:
            raise EvaluationError("Repository index is empty; run `athena scan` or use --scan")
        compiler = ContextCompiler(runtime, runtime.config.mcp.host) if mode == "economy" else None

        for case in dataset.cases:
            runtime.clear_retrieval_caches()
            context_call: Callable[[], ContextBundle] = (
                partial(_compile_economy_bundle, compiler, case.query)
                if compiler is not None
                else partial(runtime.context, case.query, profile=case.profile)
            )
            started = time.perf_counter()
            bundle = context_call()
            cold_ms = (time.perf_counter() - started) * 1000
            latency["context_cold"].append(cold_ms)
            results.append(_evaluate_bundle(case, bundle, cold_ms, runtime.store))
            latency["context_warm"].extend(
                _warm_samples(
                    context_call,
                    settings.warmup,
                    settings.iterations,
                )
            )

            terms = exact_search_terms(case.query)
            runtime.store.clear_caches()
            exact_cold, exact_warm = _operation_samples(
                partial(
                    runtime.store.exact_nodes,
                    terms,
                    runtime.config.retrieval.top_k_exact * 2,
                ),
                settings.warmup,
                settings.iterations,
            )
            latency["exact_lookup_cold"].append(exact_cold)
            latency["exact_lookup_warm"].extend(exact_warm)

            runtime.store.clear_caches()
            fts_cold, fts_warm = _operation_samples(
                partial(
                    runtime.store.lexical_chunks,
                    case.query,
                    runtime.config.retrieval.top_k_lexical,
                ),
                settings.warmup,
                settings.iterations,
            )
            latency["fts_cold"].append(fts_cold)
            latency["fts_warm"].extend(fts_warm)

            seeds = [
                node.node_id
                for node, _ in runtime.store.exact_nodes(
                    terms, runtime.config.retrieval.top_k_exact
                )
                if node.path != "@persona"
            ]
            persona = bundle.persona
            depth = min(persona.policy.graph_depth, runtime.config.retrieval.graph_depth)
            runtime.store.clear_caches()
            graph_cold, graph_warm = _operation_samples(
                partial(
                    runtime.store.graph_walk,
                    seeds,
                    persona.policy.traverse_relations,
                    depth,
                    runtime.config.retrieval.graph_max_nodes,
                ),
                settings.warmup,
                settings.iterations,
            )
            latency["graph_walk_cold"].append(graph_cold)
            latency["graph_walk_warm"].extend(graph_warm)

        scan_cold, scan_warm = _operation_samples(
            runtime.scan, settings.warmup, settings.iterations
        )
        latency["no_change_scan"].extend([scan_cold, *scan_warm])
        cache_status = runtime.status()["caches"]

    quality = _quality_report(results)
    latency_report = {name: _latency_summary(values) for name, values in latency.items()}
    report: dict[str, Any] = {
        "schema_version": 1,
        "dataset": dataset.name,
        "athena_version": __version__,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "benchmark": settings.model_dump(mode="json"),
        "mode": mode,
        "summary": quality["summary"],
        "latency": latency_report,
        "cases": quality["cases"],
        "caches": cache_status,
    }
    report["gate"] = evaluate_gates(report, dataset.thresholds)
    return report


def _compile_economy_bundle(
    compiler: ContextCompiler,
    query: str,
) -> ContextBundle:
    return compiler.compile(query).bundle


def evaluate_gates(report: dict[str, Any], thresholds: EvaluationThresholds) -> dict[str, Any]:
    summary = report["summary"]
    latency = report["latency"]
    checks: dict[str, dict[str, Any]] = {}

    def minimum(name: str, actual: float | int | None, required: float | int | None) -> None:
        if required is not None:
            passed = actual is not None and actual >= required
            checks[name] = {"actual": actual, "minimum": required, "passed": passed}

    def maximum(name: str, actual: float | int | None, required: float | int | None) -> None:
        if required is not None:
            passed = actual is not None and actual <= required
            checks[name] = {"actual": actual, "maximum": required, "passed": passed}

    minimum("routing_accuracy", summary["routing_accuracy"], thresholds.routing_accuracy_min)
    minimum("file_precision", summary["file_precision"], thresholds.file_precision_min)
    minimum("file_recall", summary["file_recall"], thresholds.file_recall_min)
    minimum("symbol_recall", summary["symbol_recall"], thresholds.symbol_recall_min)
    minimum(
        "context_type_recall",
        summary["context_type_recall"],
        thresholds.context_type_recall_min,
    )
    minimum("mrr", summary["mrr"], thresholds.mrr_min)
    maximum("forbidden_hits", summary["forbidden_hits"], thresholds.forbidden_hits_max)
    maximum(
        "max_estimated_tokens",
        summary["max_estimated_tokens"],
        thresholds.max_estimated_tokens,
    )
    maximum(
        "exact_p95_ms",
        latency["exact_lookup_warm"]["p95_ms"],
        thresholds.exact_p95_ms_max,
    )
    maximum("fts_p95_ms", latency["fts_warm"]["p95_ms"], thresholds.fts_p95_ms_max)
    maximum(
        "graph_p95_ms",
        latency["graph_walk_warm"]["p95_ms"],
        thresholds.graph_p95_ms_max,
    )
    maximum(
        "context_cold_p95_ms",
        latency["context_cold"]["p95_ms"],
        thresholds.context_cold_p95_ms_max,
    )
    maximum(
        "context_warm_p95_ms",
        latency["context_warm"]["p95_ms"],
        thresholds.context_warm_p95_ms_max,
    )
    maximum(
        "no_change_scan_p95_ms",
        latency["no_change_scan"]["p95_ms"],
        thresholds.no_change_scan_p95_ms_max,
    )
    failures = [name for name, check in checks.items() if not check["passed"]]
    return {"passed": not failures, "failures": failures, "checks": checks}


def _operation_samples(
    operation: Callable[[], object], warmup: int, iterations: int
) -> tuple[float, list[float]]:
    started = time.perf_counter()
    operation()
    cold = (time.perf_counter() - started) * 1000
    return cold, _warm_samples(operation, warmup, iterations)


def _warm_samples(operation: Callable[[], object], warmup: int, iterations: int) -> list[float]:
    for _ in range(warmup):
        operation()
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1000)
    return samples


def _latency_summary(values: Sequence[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    if not ordered:
        return {
            "samples": 0,
            "mean_ms": 0.0,
            "min_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }
    return {
        "samples": len(ordered),
        "mean_ms": round(mean(ordered), 3),
        "min_ms": round(ordered[0], 3),
        "p50_ms": round(_percentile(ordered, 50), 3),
        "p95_ms": round(_percentile(ordered, 95), 3),
        "p99_ms": round(_percentile(ordered, 99), 3),
        "max_ms": round(ordered[-1], 3),
    }


def _percentile(ordered: Sequence[float], percentile: float) -> float:
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _evaluate_bundle(
    case: EvalCase, bundle: ContextBundle, latency_ms: float, store: SQLiteStore
) -> EvalResult:
    retrieved = tuple(dict.fromkeys(hit.chunk.path for hit in bundle.hits))
    symbols = tuple(
        dict.fromkeys(
            [
                *(hit.chunk.symbol_id for hit in bundle.hits if hit.chunk.symbol_id is not None),
                *(node.node_id for node in store.nodes_for_paths(retrieved)),
            ]
        )
    )
    context_types = tuple(
        dict.fromkeys(
            _context_type(hit.chunk.path, hit.chunk.language, hit.chunk.tags) for hit in bundle.hits
        )
    )
    route_correct = (
        bundle.persona.persona_id == case.expected_persona
        if case.expected_persona is not None
        else None
    )
    precision, recall, reciprocal_rank = _file_metrics(retrieved, case.expected_files)
    symbol_recall = _set_recall(symbols, case.expected_symbols, _symbol_matches)
    context_type_recall = _set_recall(
        context_types, case.expected_context_types, lambda actual, expected: actual == expected
    )
    forbidden = sum(
        1
        for path in retrieved
        if any(_path_matches(path, forbidden_path) for forbidden_path in case.forbidden_files)
    )
    return EvalResult(
        case.case_id,
        bundle.persona.persona_id,
        route_correct,
        precision,
        recall,
        symbol_recall,
        context_type_recall,
        reciprocal_rank,
        forbidden,
        round(latency_ms, 3),
        bundle.estimated_tokens,
        retrieved,
        symbols,
        context_types,
    )


def _quality_report(results: Sequence[EvalResult]) -> dict[str, Any]:
    route_values = [
        float(result.route_correct) for result in results if result.route_correct is not None
    ]
    precisions = [result.precision for result in results if result.precision is not None]
    recalls = [result.recall for result in results if result.recall is not None]
    symbol_recalls = [
        result.symbol_recall for result in results if result.symbol_recall is not None
    ]
    type_recalls = [
        result.context_type_recall for result in results if result.context_type_recall is not None
    ]
    reciprocal_ranks = [
        result.reciprocal_rank for result in results if result.reciprocal_rank is not None
    ]
    return {
        "summary": {
            "cases": len(results),
            "routing_accuracy": _optional_mean(route_values),
            "file_precision": _optional_mean(precisions),
            "file_recall": _optional_mean(recalls),
            "symbol_recall": _optional_mean(symbol_recalls),
            "context_type_recall": _optional_mean(type_recalls),
            "mrr": _optional_mean(reciprocal_ranks),
            "forbidden_hits": sum(result.forbidden_hits for result in results),
            "avg_latency_ms": round(mean(result.latency_ms for result in results), 3)
            if results
            else 0.0,
            "avg_estimated_tokens": round(mean(result.estimated_tokens for result in results), 1)
            if results
            else 0.0,
            "max_estimated_tokens": max((result.estimated_tokens for result in results), default=0),
        },
        "cases": [
            {
                "id": result.case_id,
                "persona": result.persona,
                "route_correct": result.route_correct,
                "precision": result.precision,
                "recall": result.recall,
                "symbol_recall": result.symbol_recall,
                "context_type_recall": result.context_type_recall,
                "reciprocal_rank": result.reciprocal_rank,
                "forbidden_hits": result.forbidden_hits,
                "latency_ms": result.latency_ms,
                "estimated_tokens": result.estimated_tokens,
                "retrieved_files": list(result.retrieved_files),
                "retrieved_symbols": list(result.retrieved_symbols),
                "context_types": list(result.context_types),
            }
            for result in results
        ],
    }


def _optional_mean(values: Sequence[float]) -> float | None:
    return round(mean(values), 3) if values else None


def _file_metrics(
    retrieved: tuple[str, ...], expected: tuple[str, ...]
) -> tuple[float | None, float | None, float | None]:
    if not expected:
        return None, None, None
    relevant_positions: list[int] = []
    relevant_files = 0
    for position, path in enumerate(retrieved, 1):
        if any(_path_matches(path, expected_path) for expected_path in expected):
            relevant_positions.append(position)
            relevant_files += 1
    precision = relevant_files / len(retrieved) if retrieved else 0.0
    matched_expected = sum(
        1
        for expected_path in expected
        if any(_path_matches(path, expected_path) for path in retrieved)
    )
    recall = matched_expected / len(expected)
    reciprocal_rank = 1.0 / relevant_positions[0] if relevant_positions else 0.0
    return round(precision, 3), round(recall, 3), round(reciprocal_rank, 3)


def _set_recall(
    actual: Sequence[str],
    expected: Sequence[str],
    matches: Callable[[str, str], bool],
) -> float | None:
    if not expected:
        return None
    matched = sum(
        1 for expected_value in expected if any(matches(value, expected_value) for value in actual)
    )
    return round(matched / len(expected), 3)


def _context_type(path: str, language: str, tags: Sequence[str]) -> str:
    normalized_path = path.replace("\\", "/").casefold()
    normalized_tags = {tag.casefold() for tag in tags}
    if "test" in normalized_tags or "/test/" in normalized_path or ".test." in normalized_path:
        return "test"
    if language in {"yaml", "properties"}:
        return "configuration"
    if language == "sql":
        return "database"
    if language == "markdown":
        return "documentation"
    return "source"


def _symbol_matches(actual: str, expected: str) -> bool:
    normalized_actual = actual.casefold()
    normalized_expected = expected.casefold()
    if normalized_actual == normalized_expected:
        return True
    tail = normalized_actual.rsplit("::", 1)[-1]
    return tail == normalized_expected or tail.endswith("." + normalized_expected)


def _path_matches(actual: str, expected: str) -> bool:
    normalized_actual = actual.replace("\\", "/").casefold()
    normalized_expected = expected.replace("\\", "/").casefold()
    return normalized_actual == normalized_expected or normalized_actual.endswith(
        "/" + normalized_expected
    )
