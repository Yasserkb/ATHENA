from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from mcp.types import LATEST_PROTOCOL_VERSION

from athena.application import ContextCompiler
from athena.context_projection import economy_payload
from athena.errors import AthenaError
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
        assert set(schema["properties"]) == {
            "query",
            "persona",
            "continuation_token",
            "request_kind",
        }
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


def test_clarification_is_metadata_only_bounded_and_recommends_user_input(
    tmp_path: Path,
) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        compiler = ContextCompiler(runtime, "codex")
        compiled = compiler.compile(
            "Fix this payment retry thing again",
            "developer",
            request_kind="clarify",
        )
        payload = compiled.payload

        metrics = runtime.store.observatory_metrics(tmp_path.name)

    assert payload["kind"] == "clarification"
    assert payload["ambiguous"] is True
    assert payload["recommendation"] == "ask_user"
    assert 1 <= len(payload["candidates"]) <= 3
    assert all("content" not in candidate for candidate in payload["candidates"])
    assert all("exact-symbol" not in candidate["why"] for candidate in payload["candidates"])
    assert len({candidate["path"] for candidate in payload["candidates"]}) == len(
        payload["candidates"]
    )
    assert payload["usage"]["tokens"] <= 400
    assert "continuation" not in payload
    assert metrics["savings"]["context_requests"] == 0
    assert metrics["recent"][0]["operation"] == "clarification"
    assert metrics["recent"][0]["payload"]["graph_nodes"] == 0


def test_clarification_can_converge_on_an_exact_target(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        compiled = ContextCompiler(runtime, "codex").compile(
            "Update PaymentPart0 retry_payment_0",
            "developer",
            request_kind="clarify",
        )

    assert compiled.payload["ambiguous"] is False
    assert compiled.payload["recommendation"] == "use_context"
    assert compiled.payload["candidates"][0]["path"] == "PaymentPart0.py"


def test_clarification_does_not_overtrust_one_identifier_with_vague_language(
    tmp_path: Path,
) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        compiled = ContextCompiler(runtime, "codex").compile(
            "Fix this PaymentPart0 thing",
            "developer",
            request_kind="clarify",
        )

    assert compiled.payload["ambiguous"] is True
    assert compiled.payload["recommendation"] == "ask_user"


def test_clarification_rejects_continuation_tokens(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        compiler = ContextCompiler(runtime, "codex")
        with pytest.raises(AthenaError, match="do not accept continuation"):
            compiler.compile(
                "Fix payment retry",
                continuation_token="ctx_not_allowed",
                request_kind="clarify",
            )


def test_stdio_transport_executes_clarification_on_sqlite_owner_thread(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "athena-test", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "repository_context",
                "arguments": {
                    "query": "Fix this payment retry thing again",
                    "persona": "developer",
                    "request_kind": "clarify",
                },
            },
        },
    ]
    wire_input = "\n".join(json.dumps(message) for message in messages) + "\n"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "athena",
            "mcp",
            "--root",
            str(tmp_path),
            "--mode",
            "economy",
            "--mcp-host",
            "codex",
        ],
        cwd=tmp_path,
        input=wire_input,
        text=True,
        capture_output=True,
        timeout=20,
        check=True,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    tool_response = next(response for response in responses if response.get("id") == 2)
    payload = json.loads(tool_response["result"]["content"][0]["text"])

    assert payload["kind"] == "clarification"
    assert payload["usage"]["tokens"] <= payload["usage"]["budget"]
    assert all("content" not in candidate for candidate in payload["candidates"])


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
