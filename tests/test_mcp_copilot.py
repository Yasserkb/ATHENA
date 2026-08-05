from __future__ import annotations

import asyncio
import json
from pathlib import Path

from athena.integrations import generate_adapters
from athena.mcp.server import create_server


def test_copilot_mcp_exposes_one_minimal_auto_refreshing_tool(tmp_path: Path) -> None:
    source = tmp_path / "PaymentClient.java"
    source.write_text(
        "class PaymentClient { void retryPayment() {} }\n",
        encoding="utf-8",
    )
    server = create_server(tmp_path, copilot_mode=True)

    async def exercise() -> None:
        tools = await server.list_tools()
        assert [tool.name for tool in tools] == ["athena_context"]
        assert tools[0].inputSchema["required"] == ["task"]
        assert set(tools[0].inputSchema["properties"]) == {
            "task",
            "persona",
            "request_kind",
        }

        result = await server._tool_manager.call_tool(
            "athena_context",
            {"task": "Fix PaymentClient retryPayment", "persona": "developer"},
            convert_result=False,
        )
        payload = json.loads(result.content[0].text)
        assert payload["usage"]["budget"] == 1400
        assert payload["usage"]["scope"] == "mcp-call-tool-result-only"
        assert payload["evidence"]
        assert payload["evidence"][0]["path"] == "PaymentClient.java"

        clarification = await server._tool_manager.call_tool(
            "athena_context",
            {"task": "Fix this payment thing again", "request_kind": "clarify"},
            convert_result=False,
        )
        clarification_text = clarification.content[0].text
        clarification_payload = json.loads(clarification_text)
        assert clarification_payload["kind"] == "clarification"
        assert clarification_payload["usage"]["budget"] == 400
        assert "void retryPayment" not in clarification_text

    asyncio.run(exercise())


def test_generated_copilot_ide_adapters_enable_dynamic_mcp_mode(tmp_path: Path) -> None:
    outputs = generate_adapters(tmp_path)
    vscode = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    jetbrains = json.loads(
        (tmp_path / ".athena" / "jetbrains-copilot-mcp.json").read_text(encoding="utf-8")
    )
    instructions = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    codex = (tmp_path / ".athena" / "codex-mcp-config.toml").read_text(encoding="utf-8")

    assert len(outputs) == 6
    assert vscode["servers"]["athena"]["args"][-4:] == [
        "--copilot",
        "--daemon",
        "--mcp-host",
        "vscode-copilot",
    ]
    assert jetbrains["servers"]["athena"]["args"][-4:] == [
        "--copilot",
        "--daemon",
        "--mcp-host",
        "jetbrains-copilot",
    ]
    assert jetbrains["servers"]["athena"]["args"][2] == str(tmp_path.resolve())
    assert "call `athena_context` exactly" in instructions
    assert '--mode", "economy"' in codex
    assert 'enabled_tools = ["repository_context"]' in codex
