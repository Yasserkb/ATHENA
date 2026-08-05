from __future__ import annotations

import atexit
from pathlib import Path
from typing import Any, Literal

from athena.application import ContextCompiler
from athena.daemon import ensure_daemon_running, load_daemon_diagnostics
from athena.mcp_envelope import MCPHost
from athena.orchestrator import AthenaRuntime
from athena.retrieval import RetrievalRequestKind
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
        "For a vague repository task, call repository_context once with request_kind='clarify'; "
        "use its candidate targets to focus the query, or ask the user when recommendation is "
        "ask_user. Clarification returns metadata only and never accepts continuation. For a "
        "specific task, call repository_context once with request_kind='context' before broad "
        "exploration. Reuse its evidence and use continuation only when it is insufficient. Skip "
        "Athena for general questions; verify exact source before edits when confidence is low."
        if effective_mode == "economy" and not copilot_mode
        else (
            "For a vague repository task, call athena_context with request_kind='clarify' and ask "
            "one question when it recommends ask_user; otherwise make a focused context call. "
            "For a specific repository task, call athena_context with request_kind='context' once "
            "before broad exploration. Reuse its evidence and skip it for general questions."
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
            async def copilot_context(
                task: str,
                persona: str | None = None,
                request_kind: RetrievalRequestKind = "context",
            ) -> Any:
                """Return bounded repository evidence for this coding task."""
                return compiler.compile(task, persona, request_kind=request_kind).mcp_result()

            return mcp

        @mcp.tool(name="repository_context", annotations=annotations, structured_output=False)
        async def repository_context(
            query: str,
            persona: str | None = None,
            continuation_token: str | None = None,
            request_kind: RetrievalRequestKind = "context",
        ) -> Any:
            """Return compact evidence, or metadata-only targets when the query is vague."""
            return compiler.compile(
                query,
                persona,
                continuation_token,
                request_kind,
            ).mcp_result()

        return mcp

    @mcp.tool(name="athena_scan_repository")
    async def scan_repository() -> dict[str, Any]:
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
    async def build_context(
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
    async def inspect_graph(name: str, limit: int = 50) -> list[dict[str, Any]]:
        """Inspect typed incoming and outgoing graph relations for a symbol or configuration key."""
        return runtime.graph(name, max(1, min(limit, 100)))

    @mcp.tool(name="athena_status")
    async def status() -> dict[str, Any]:
        """Show index freshness, statistics, workspace restrictions, and available personas."""
        return runtime.status()

    @mcp.tool(name="athena_list_personas")
    async def list_personas() -> list[dict[str, Any]]:
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
    async def diagnostics() -> dict[str, Any]:
        """Read watcher, indexing, and parse diagnostics produced by the Athena daemon."""
        return load_daemon_diagnostics(runtime.root)

    @mcp.resource("athena://persona/{persona_id}")
    async def persona_resource(persona_id: str) -> str:
        """Read one effective persona card without loading all framework documentation."""
        return runtime.persona(persona_id).prompt_card()

    @mcp.prompt(name="athena_task")
    async def task_prompt(
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
