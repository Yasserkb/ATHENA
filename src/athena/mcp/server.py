from __future__ import annotations

import atexit
from pathlib import Path
from typing import Any, Literal

from athena.application import ContextCompiler
from athena.daemon import ensure_daemon_running, load_daemon_diagnostics
from athena.mcp_envelope import MCPHost
from athena.orchestrator import AthenaRuntime
from athena.tokenization import TokenizerProvider


def create_server(
    root: Path,
    copilot_mode: bool = False,
    mcp_host: MCPHost | None = None,
    mode: Literal["full", "economy"] | None = None,
) -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit('MCP support requires: pip install -e ".[mcp]"') from exc

    runtime = AthenaRuntime(root)
    effective_host = mcp_host or runtime.config.mcp.host
    effective_mode = "economy" if copilot_mode else (mode or runtime.config.mcp.mode)
    atexit.register(runtime.close)
    instructions = (
        "For repository work, call repository_context once before broad exploration. Reuse its "
        "evidence. Use its continuation only when evidence is insufficient. Skip it for general "
        "questions; verify exact source before edits when confidence is low."
        if effective_mode == "economy" and not copilot_mode
        else (
            "For repository work, call athena_context once before broad exploration. Reuse its "
            "evidence and skip it for general questions."
            if copilot_mode
            else (
                "Local, evidence-backed code graph. Build context before repository changes. "
                "The server does not execute arbitrary shell commands."
            )
        )
    )
    mcp = FastMCP(
        "Athena CodeGraph",
        instructions=instructions,
        json_response=True,
    )

    if effective_mode == "economy":
        compiler = ContextCompiler(runtime, effective_host)
        annotations = ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )

        if copilot_mode:

            @mcp.tool(name="athena_context", annotations=annotations, structured_output=False)
            def copilot_context(task: str, persona: str | None = None) -> Any:
                """Return bounded repository evidence for this coding task."""
                return compiler.compile(task, persona).mcp_result()

            return mcp

        @mcp.tool(name="repository_context", annotations=annotations, structured_output=False)
        def repository_context(
            query: str,
            persona: str | None = None,
            continuation_token: str | None = None,
        ) -> Any:
            """Return compact repository evidence; call once before broad exploration."""
            return compiler.compile(query, persona, continuation_token).mcp_result()

        return mcp

    @mcp.tool(name="athena_scan_repository")
    def scan_repository() -> dict[str, Any]:
        """Incrementally analyze the allowed workspace and refresh its local graph index."""
        report = runtime.scan()
        return {
            "repository": report.repository,
            "scanned": report.scanned,
            "unchanged": report.unchanged,
            "deleted": report.deleted,
            "chunks": report.chunks,
            "nodes": report.nodes,
            "edges": report.edges,
            "duration_ms": report.duration_ms,
            "warnings": list(report.warnings),
        }

    @mcp.tool(name="athena_build_context")
    def build_context(
        task: str,
        persona: str | None = None,
        profile: str | None = None,
        tokenizer_provider: TokenizerProvider | None = None,
        target_model: str | None = None,
        allow_remote_token_counting: bool | None = None,
    ) -> dict[str, Any]:
        """Return the smallest persona-aware architecture and source context for a task."""
        return runtime.context(
            task,
            persona,
            profile,
            tokenizer_provider,
            target_model,
            allow_remote_token_counting,
            effective_host,
        ).to_dict()

    @mcp.tool(name="athena_inspect_graph")
    def inspect_graph(name: str, limit: int = 50) -> list[dict[str, Any]]:
        """Inspect typed incoming and outgoing graph relations for a symbol or configuration key."""
        return runtime.graph(name, max(1, min(limit, 100)))

    @mcp.tool(name="athena_status")
    def status() -> dict[str, Any]:
        """Show index freshness, statistics, workspace restrictions, and available personas."""
        return runtime.status()

    @mcp.tool(name="athena_list_personas")
    def list_personas() -> list[dict[str, Any]]:
        """List persona purposes and retrieval budgets."""
        return [
            {
                "id": persona.persona_id,
                "purpose": persona.purpose,
                "max_context_tokens": persona.policy.max_context_tokens,
                "graph_depth": persona.policy.graph_depth,
            }
            for persona in runtime.personas.all().values()
        ]

    @mcp.tool(name="athena_diagnostics")
    def diagnostics() -> dict[str, Any]:
        """Read watcher, indexing, and parse diagnostics produced by the Athena daemon."""
        return load_daemon_diagnostics(runtime.root)

    @mcp.resource("athena://persona/{persona_id}")
    def persona_resource(persona_id: str) -> str:
        """Read one effective persona card without loading all framework documentation."""
        return runtime.persona(persona_id).prompt_card()

    @mcp.prompt(name="athena_task")
    def task_prompt(
        task: str,
        persona: str = "",
        tokenizer_provider: TokenizerProvider | None = None,
        target_model: str | None = None,
        allow_remote_token_counting: bool | None = None,
    ) -> str:
        """Build a ready-to-use task prompt from indexed evidence."""
        return runtime.context(
            task,
            persona or None,
            tokenizer_provider=tokenizer_provider,
            target_model=target_model,
            allow_remote_token_counting=allow_remote_token_counting,
        ).to_prompt()

    return mcp


def run_server(
    root: Path,
    copilot_mode: bool = False,
    ensure_daemon: bool = False,
    mcp_host: MCPHost | None = None,
    mode: Literal["full", "economy"] | None = None,
) -> None:
    if ensure_daemon:
        ensure_daemon_running(root)
    create_server(root, copilot_mode, mcp_host, mode).run(transport="stdio")
