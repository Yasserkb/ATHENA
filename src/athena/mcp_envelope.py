from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

MCPHost = Literal[
    "generic-mcp",
    "vscode-copilot",
    "jetbrains-copilot",
    "claude-code",
    "codex",
]


@dataclass(frozen=True, slots=True)
class HostEnvelopeProfile:
    host: MCPHost
    format: str
    scope: str = "mcp-call-tool-result-only"
    deterministic: bool = True


def host_envelope_profile(host: MCPHost) -> HostEnvelopeProfile:
    """Describe the deterministic server-result boundary available for a host."""
    return HostEnvelopeProfile(host, f"{host}:mcp-call-tool-result-v1")


def serialize_host_envelope(payload: dict[str, Any], host: MCPHost) -> str:
    """Serialize FastMCP's deterministic CallToolResult for a structured result.

    The host label records the integration in use. Private conversation/model framing and
    request-specific JSON-RPC IDs remain outside this honest accounting boundary.
    """
    host_envelope_profile(host)
    text_copy = json.dumps(payload, ensure_ascii=True, indent=2)
    result = {
        "content": [{"type": "text", "text": text_copy}],
        "structuredContent": payload,
        "isError": False,
    }
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def serialize_text_host_envelope(text: str, host: MCPHost) -> str:
    """Serialize a text-only CallToolResult containing one canonical payload copy."""
    host_envelope_profile(host)
    result = {
        "content": [{"type": "text", "text": text}],
        "isError": False,
    }
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))
