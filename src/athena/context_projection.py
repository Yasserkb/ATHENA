from __future__ import annotations

import json
from typing import Any, Literal

from athena.domain import ContextBundle
from athena.mcp_envelope import MCPHost, serialize_host_envelope, serialize_text_host_envelope

ProjectionId = Literal[
    "full-v1",
    "athena-context-economy-v1",
    "athena-clarification-v1",
]
ResponseRepresentation = Literal["structured-compat-v1", "compact-text-v1"]

ECONOMY_PROJECTION: ProjectionId = "athena-context-economy-v1"
CLARIFICATION_PROJECTION: ProjectionId = "athena-clarification-v1"
FULL_PROJECTION: ProjectionId = "full-v1"


def economy_payload(bundle: ContextBundle) -> dict[str, Any]:
    """Project a full internal bundle into the smallest stable agent-facing contract."""
    payload: dict[str, Any] = {
        "v": 1,
        "persona": bundle.persona.persona_id,
        "confidence": bundle.retrieval_confidence,
        "evidence": [
            {
                "path": hit.chunk.path,
                "lines": [hit.chunk.start_line, hit.chunk.end_line],
                "score": round(hit.score, 4),
                "why": list(hit.reasons),
                "content": hit.chunk.content,
            }
            for hit in bundle.hits
        ],
        "usage": {
            "tokens": bundle.provider_tokens or bundle.estimated_tokens,
            "budget": bundle.hard_budget,
            "remaining": bundle.remaining_budget,
            "dropped": bundle.dropped_evidence,
            "scope": bundle.accounting_scope,
        },
    }
    if bundle.architecture:
        payload["architecture"] = list(bundle.architecture)
    if bundle.warnings:
        payload["warnings"] = list(bundle.warnings)
    if bundle.continuation_token:
        payload["continuation"] = bundle.continuation_token
    if bundle.incremental_files_scanned:
        payload["refresh"] = {"scanned": bundle.incremental_files_scanned}
    return payload


def clarification_payload(bundle: ContextBundle) -> dict[str, Any]:
    """Return target metadata only so ambiguity checks never load source bodies."""
    assessment = bundle.query_assessment
    if assessment is None:
        raise ValueError("clarification projection requires a query assessment")
    payload: dict[str, Any] = {
        "v": 1,
        "kind": "clarification",
        "ambiguous": assessment.ambiguous,
        "recommendation": assessment.recommendation,
        "confidence": assessment.confidence,
        "reasons": list(assessment.reasons),
        "candidates": [
            {
                "path": hit.chunk.path,
                "lines": [hit.chunk.start_line, hit.chunk.end_line],
                "symbol": hit.chunk.symbol_id,
                "score": round(hit.score, 4),
                "why": list(hit.reasons),
            }
            for hit in bundle.hits
        ],
        "usage": {
            "tokens": bundle.provider_tokens or bundle.estimated_tokens,
            "budget": bundle.hard_budget,
            "remaining": bundle.remaining_budget,
            "dropped": bundle.dropped_evidence,
            "scope": bundle.accounting_scope,
        },
    }
    if bundle.warnings:
        payload["warnings"] = list(bundle.warnings)
    return payload


def projection_payload(bundle: ContextBundle) -> dict[str, Any]:
    if bundle.projection_id == CLARIFICATION_PROJECTION:
        return clarification_payload(bundle)
    if bundle.projection_id == ECONOMY_PROJECTION:
        return economy_payload(bundle)
    return bundle.to_dict()


def projection_json(bundle: ContextBundle) -> str:
    payload = projection_payload(bundle)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def serialize_projected_result(bundle: ContextBundle, host: MCPHost | None) -> str:
    """Serialize the exact Athena-controlled result boundary used for budgeting."""
    payload = projection_payload(bundle)
    if host is None:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if bundle.response_representation == "compact-text-v1":
        return serialize_text_host_envelope(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
            host,
        )
    return serialize_host_envelope(payload, host)


def mcp_text_result(bundle: ContextBundle) -> Any:
    """Build the SDK result used by compact-text-v1 without importing MCP at package import."""
    from mcp.types import CallToolResult, TextContent

    return CallToolResult(
        content=[TextContent(type="text", text=projection_json(bundle))],
        isError=False,
    )
