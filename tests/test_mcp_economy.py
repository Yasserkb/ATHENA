from __future__ import annotations

import asyncio
import json
from pathlib import Path

from athena.application import ContextCompiler
from athena.context_projection import economy_payload
from athena.mcp.server import create_server
from athena.orchestrator import AthenaRuntime


def _write_repository(root: Path) -> None:
    for index in range(6):
        (root / f"PaymentPart{index}.py").write_text(
            f"class PaymentPart{index}:\n"
            f"    def retry_payment_{index}(self):\n"
            f"        return 'payment-{index}'\n",
            encoding="utf-8",
        )


def test_neutral_economy_server_exposes_one_small_tool(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    server = create_server(tmp_path, mode="economy", mcp_host="codex")

    async def exercise() -> None:
        tools = await server.list_tools()
        assert [tool.name for tool in tools] == ["repository_context"]
        schema = tools[0].inputSchema
        assert schema["required"] == ["query"]
        assert set(schema["properties"]) == {"query", "persona", "continuation_token"}
        assert tools[0].annotations is not None
        assert tools[0].annotations.readOnlyHint is False
        assert tools[0].annotations.destructiveHint is False
        result = await server._tool_manager.call_tool(
            "repository_context",
            {"query": "Fix PaymentPart0 retry_payment_0", "persona": "developer"},
            convert_result=False,
        )
        payload = json.loads(result.content[0].text)
        assert payload["v"] == 1
        assert "repository" not in payload
        assert "query" not in payload
        assert "persona_card" not in payload
        assert payload["usage"]["tokens"] <= payload["usage"]["budget"]
        assert payload["usage"]["scope"] == "mcp-call-tool-result-only"
        assert payload["continuation"].startswith("ctx_")
        assert payload["evidence"][0]["path"] == "PaymentPart0.py"

    asyncio.run(exercise())


def test_continuation_excludes_previously_returned_chunks(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        compiler = ContextCompiler(runtime, "codex")
        first = compiler.compile("Trace payment retry flow", "developer")
        token = str(economy_payload(first.bundle)["continuation"])
        second = compiler.compile("Show remaining related implementation", continuation_token=token)

    first_ids = {hit.chunk.chunk_id for hit in first.bundle.hits}
    second_ids = {hit.chunk.chunk_id for hit in second.bundle.hits}
    assert first_ids
    assert first_ids.isdisjoint(second_ids)


def test_compact_text_result_is_smaller_than_full_structured_result(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        full = runtime.context(
            "Fix PaymentPart0 retry_payment_0",
            "developer",
            tokenizer_provider="generic",
            mcp_host="codex",
        )
        compiler = ContextCompiler(runtime, "codex")
        compact = compiler.compile("Fix PaymentPart0 retry_payment_0", "developer").bundle

    assert compact.accounted_bytes < full.accounted_bytes
    assert compact.estimated_tokens < full.estimated_tokens
    assert compact.response_representation == "compact-text-v1"
    assert compact.projection_id == "athena-context-economy-v1"
