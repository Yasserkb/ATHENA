from __future__ import annotations

import json
from pathlib import Path

import pytest

from athena.config import AppConfig
from athena.mcp_envelope import (
    host_envelope_profile,
    serialize_host_envelope,
    serialize_text_host_envelope,
)
from athena.orchestrator import AthenaRuntime
from athena.tokenization import estimate_tokens


def test_deterministic_envelope_matches_mcp_sdk_result_body() -> None:
    types = pytest.importorskip("mcp.types")
    payload = {"repository": "sample", "task": "Inspect Caf\u00e9Service", "evidence": []}
    expected = types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=True, indent=2),
            )
        ],
        structuredContent=payload,
        isError=False,
    ).model_dump_json(by_alias=True, exclude_none=True)

    assert serialize_host_envelope(payload, "generic-mcp") == expected


def test_text_envelope_matches_mcp_sdk_and_contains_payload_once() -> None:
    types = pytest.importorskip("mcp.types")
    text = '{"evidence":[{"content":"unique-marker"}],"v":1}'
    expected = types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        isError=False,
    ).model_dump_json(by_alias=True, exclude_none=True)

    actual = serialize_text_host_envelope(text, "codex")
    assert actual == expected
    assert actual.count("unique-marker") == 1


def test_host_envelope_is_included_in_hard_budget_and_cache_identity(tmp_path: Path) -> None:
    (tmp_path / "Service.py").write_text(
        "class Service:\n    def execute(self):\n        return 1\n",
        encoding="utf-8",
    )
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        bare = runtime.context(
            "Update Service execute",
            "developer",
            tokenizer_provider="generic",
        )
        hosted = runtime.context(
            "Update Service execute",
            "developer",
            tokenizer_provider="generic",
            mcp_host="vscode-copilot",
        )

        envelope = serialize_host_envelope(hosted.to_dict(), "vscode-copilot")
        assert hosted is not bare
        assert hosted.mcp_host == "vscode-copilot"
        assert hosted.accounting_format == "vscode-copilot:mcp-call-tool-result-v1"
        assert hosted.accounting_scope == "mcp-call-tool-result-only"
        assert hosted.accounted_bytes == len(envelope.encode("utf-8"))
        assert hosted.estimated_tokens == estimate_tokens(envelope)
        assert hosted.host_envelope_overhead_estimated_tokens == (
            hosted.estimated_tokens - estimate_tokens(hosted.to_json())
        )
        assert hosted.accounted_bytes > hosted.serialized_bytes
        assert hosted.estimated_tokens > bare.estimated_tokens
        assert hosted.remaining_budget == hosted.hard_budget - hosted.estimated_tokens
        assert hosted.remaining_budget >= 0


def test_supported_hosts_have_explicit_deterministic_scope() -> None:
    for host in (
        "generic-mcp",
        "vscode-copilot",
        "jetbrains-copilot",
        "claude-code",
        "codex",
    ):
        profile = host_envelope_profile(host)
        assert profile.deterministic is True
        assert profile.scope == "mcp-call-tool-result-only"
        assert profile.format.endswith(":mcp-call-tool-result-v1")


def test_mcp_host_configuration_is_strict() -> None:
    assert AppConfig.model_validate({"mcp": {"host": "codex"}}).mcp.host == "codex"
    with pytest.raises(ValueError):
        AppConfig.model_validate({"mcp": {"host": "unknown-host"}})
