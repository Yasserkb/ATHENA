from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

NodeKind = Literal[
    "repository",
    "package",
    "file",
    "class",
    "interface",
    "record",
    "enum",
    "method",
    "annotation",
    "endpoint",
    "configuration_key",
    "environment_variable",
    "database_table",
    "migration",
    "test",
    "pattern",
    "workflow",
    "external_symbol",
    "persona",
    "relation_policy",
    "node_kind_policy",
    "tag_policy",
]


@dataclass(frozen=True, slots=True)
class Evidence:
    path: str
    start_line: int
    end_line: int
    content_hash: str
    extractor: str
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    kind: str
    name: str
    qualified_name: str
    path: str | None = None
    start_line: int = 0
    end_line: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Edge:
    source_id: str
    relation: str
    target_id: str
    evidence: Evidence
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Symbol:
    node: GraphNode
    signature: str = ""
    body_start_line: int = 0
    body_end_line: int = 0


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    content: str
    content_hash: str
    symbol_id: str | None = None
    language: str = "text"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: str
    absolute_path: Path
    content_hash: str
    size_bytes: int
    modified_ns: int
    language: str


@dataclass(frozen=True, slots=True)
class IndexedFileAnalysis:
    file: FileRecord
    nodes: tuple[GraphNode, ...]
    edges: tuple[Edge, ...]
    chunks: tuple[Chunk, ...]


@dataclass(frozen=True, slots=True)
class ScanReport:
    repository: str
    scanned: int
    unchanged: int
    deleted: int
    chunks: int
    nodes: int
    edges: int
    duration_ms: float
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    chunk: Chunk
    score: float
    reasons: tuple[str, ...]
    graph_distance: int | None = None


@dataclass(frozen=True, slots=True)
class QueryAssessment:
    """Deterministic assessment used to resolve an underspecified repository request."""

    ambiguous: bool
    recommendation: Literal["use_context", "ask_user"]
    confidence: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PersonaRetrievalPolicy:
    start_kinds: tuple[str, ...] = ()
    traverse_relations: tuple[str, ...] = ()
    include_tags: tuple[str, ...] = ()
    max_context_tokens: int = 2400
    max_chunks_per_file: int = 3
    graph_depth: int = 2


@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str
    purpose: str
    triggers: tuple[str, ...]
    rules: tuple[str, ...]
    output: str
    policy: PersonaRetrievalPolicy

    def prompt_card(self) -> str:
        """Return the bounded, task-facing part of a persona.

        Full persona playbooks are indexed as knowledge. Keeping the MCP card concise reserves
        the hard context budget for repository evidence, including for deliberately small
        budgets used by economy-mode callers.
        """
        lines = [f"# Mode: {self.persona_id}", self.purpose]
        if self.rules:
            lines.append("Rules:")
            card_rules = self.rules[:4]
            lines.extend(f"- {rule}" for rule in card_rules)
            if len(self.rules) > len(card_rules):
                lines.append("- Apply the persona's indexed playbooks when they are relevant.")
        lines.append(f"Output: {self.output}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ContextBundle:
    repository: str
    task: str
    persona: Persona
    hits: tuple[RetrievalHit, ...]
    architecture: tuple[str, ...]
    estimated_tokens: int
    retrieval_confidence: float
    warnings: tuple[str, ...] = ()
    profile: str = "balanced"
    exact_tokens: int | None = None
    provider_tokens: int | None = None
    tokenizer: str = "estimated:utf8-bytes-v1"
    token_count_source: str = "heuristic-estimate"
    target_model: str | None = None
    hard_budget: int = 0
    remaining_budget: int = 0
    serialized_bytes: int = 0
    payload_format: str = "athena-mcp-json-v1"
    mcp_host: str | None = None
    accounting_format: str = "athena-mcp-json-v1"
    accounting_scope: str = "athena-tool-result-only"
    accounted_bytes: int = 0
    host_envelope_overhead_estimated_tokens: int = 0
    dropped_evidence: int = 0
    estimated_input_ai_credits: float | None = None
    monthly_ai_credit_budget: int | None = None
    estimated_monthly_athena_payloads: int | None = None
    ai_credit_scope: str | None = None
    projection_id: str = "full-v1"
    response_representation: str = "structured-compat-v1"
    continuation_token: str | None = None
    incremental_files_scanned: int = 0
    query_assessment: QueryAssessment | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "repository": self.repository,
            "task": self.task,
            "persona": self.persona.persona_id,
            "profile": self.profile,
            "persona_card": self.persona.prompt_card(),
            "architecture": list(self.architecture),
            "estimated_tokens": self.estimated_tokens,
            "exact_tokens": self.exact_tokens,
            "provider_tokens": self.provider_tokens,
            "tokenizer": self.tokenizer,
            "token_count_source": self.token_count_source,
            "target_model": self.target_model,
            "hard_budget": self.hard_budget,
            "remaining_budget": self.remaining_budget,
            "serialized_bytes": self.serialized_bytes,
            "payload_format": self.payload_format,
            "mcp_host": self.mcp_host,
            "accounting_format": self.accounting_format,
            "accounting_scope": self.accounting_scope,
            "accounted_bytes": self.accounted_bytes,
            "host_envelope_overhead_estimated_tokens": (
                self.host_envelope_overhead_estimated_tokens
            ),
            "dropped_evidence": self.dropped_evidence,
            "estimated_input_ai_credits": self.estimated_input_ai_credits,
            "monthly_ai_credit_budget": self.monthly_ai_credit_budget,
            "estimated_monthly_athena_payloads": self.estimated_monthly_athena_payloads,
            "ai_credit_scope": self.ai_credit_scope,
            "retrieval_confidence": self.retrieval_confidence,
            "warnings": list(self.warnings),
            "evidence": [
                {
                    "path": hit.chunk.path,
                    "start_line": hit.chunk.start_line,
                    "end_line": hit.chunk.end_line,
                    "score": round(hit.score, 6),
                    "reasons": list(hit.reasons),
                    "detail": "compressed"
                    if "compressed-secondary-evidence" in hit.reasons
                    else "full",
                    "content": hit.chunk.content,
                }
                for hit in self.hits
            ],
        }
        if self.query_assessment is not None:
            result["query_assessment"] = {
                "ambiguous": self.query_assessment.ambiguous,
                "recommendation": self.query_assessment.recommendation,
                "confidence": self.query_assessment.confidence,
                "reasons": list(self.query_assessment.reasons),
            }
        return result

    def to_json(self, *, pretty: bool = False) -> str:
        """Serialize the exact Athena-controlled MCP/JSON result representation."""
        if pretty:
            return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def to_prompt(self) -> str:
        sections = [self.persona.prompt_card()]
        if self.architecture:
            sections.append("## Architecture\n" + "\n".join(f"- {x}" for x in self.architecture))
        if self.hits:
            evidence = []
            for hit in self.hits:
                evidence.append(
                    f"### {hit.chunk.path}:{hit.chunk.start_line}-{hit.chunk.end_line} "
                    f"[score={hit.score:.3f}; {', '.join(hit.reasons)}]\n"
                    f"```{hit.chunk.language}\n{hit.chunk.content.rstrip()}\n```"
                )
            sections.append("## Evidence\n" + "\n\n".join(evidence))
        if self.warnings:
            sections.append("## Retrieval warnings\n" + "\n".join(f"- {x}" for x in self.warnings))
        sections.append("## Task\n" + self.task.strip())
        return "\n\n".join(sections)
