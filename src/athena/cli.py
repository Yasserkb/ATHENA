from __future__ import annotations

import json
import shutil
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

import typer
import yaml

from athena import __version__
from athena.application import ContextCompiler
from athena.config import AppConfig, database_path, load_config
from athena.daemon import (
    DaemonService,
    ensure_daemon_running,
    load_daemon_diagnostics,
    load_daemon_status,
    request_daemon_stop,
)
from athena.errors import AthenaError
from athena.evaluation import (
    evaluation_schema,
    load_cases,
    load_dataset,
    run_benchmark,
    run_evaluation,
)
from athena.git_sync import sync_repository
from athena.graph import export_graph
from athena.indexing.scanner import git_head
from athena.indexing.semantic import SemanticPluginRegistry
from athena.integrations import generate_adapters
from athena.mcp_envelope import MCPHost, host_envelope_profile
from athena.observatory import ProjectRegistry, run_observatory
from athena.orchestrator import AthenaRuntime
from athena.personas import install_persona_knowledge
from athena.tokenization import TokenizerProvider

app = typer.Typer(
    name="athena",
    help="Evidence-backed code graph and persona-aware context for coding assistants.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
daemon_app = typer.Typer(help="Run and manage the persistent repository watcher.")
observatory_app = typer.Typer(help="Run the local multi-repository Athena dashboard.")
app.add_typer(daemon_app, name="daemon")
app.add_typer(observatory_app, name="observatory")

RootOption = Annotated[Path, typer.Option("--root", "-r", help="Repository root")]


def _root(value: Path) -> Path:
    return value.expanduser().resolve()


def _run(action: Callable[[], None]) -> None:
    try:
        action()
    except AthenaError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2) from exc


@app.command()
def version() -> None:
    """Print the runtime version."""
    typer.echo(__version__)


@app.command()
def init(
    root: Annotated[Path, typer.Argument(help="Repository root")] = Path("."),
    force: Annotated[bool, typer.Option("--force", help="Replace an existing config")] = False,
) -> None:
    """Create repository-local Athena configuration and thin IDE adapters."""
    root = _root(root)
    root.mkdir(parents=True, exist_ok=True)
    athena_dir = root / ".athena"
    config_path = athena_dir / "config.yaml"
    if config_path.exists() and not force:
        typer.echo(f"Configuration already exists: {config_path}")
    else:
        athena_dir.mkdir(parents=True, exist_ok=True)
        (athena_dir / "personas").mkdir(exist_ok=True)
        config = AppConfig().model_dump(mode="json")
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        typer.echo(f"Created {config_path}")
    for path in install_persona_knowledge(root, overwrite=force):
        typer.echo(f"Installed {path.relative_to(root)}")
    for path in generate_adapters(root):
        typer.echo(f"Generated {path.relative_to(root)}")
    registered = ProjectRegistry().add(root)
    typer.echo(f"Registered {registered.root} with Athena Observatory")


@observatory_app.command("start")
def observatory_start(
    root: RootOption = Path("."),
    host: Annotated[
        str, typer.Option("--host", help="Listening interface; keep 127.0.0.1 for local-only use")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", min=0, max=65535)] = 8765,
    open_browser: Annotated[
        bool, typer.Option("--open/--no-open", help="Open the dashboard in the default browser")
    ] = True,
    registry: Annotated[
        Path | None, typer.Option("--registry", help="Override the local project registry path")
    ] = None,
) -> None:
    """Start Athena Observatory and register the selected repository."""

    def action() -> None:
        run_observatory(
            _root(root),
            host=host,
            port=port,
            open_browser=open_browser,
            registry_path=registry,
        )

    _run(action)


@observatory_app.command("add")
def observatory_add(
    root: Annotated[Path, typer.Argument(help="Repository root")],
    database: Annotated[
        Path | None,
        typer.Option("--database", help="Explicit SQLite index path for external state"),
    ] = None,
    registry: Annotated[Path | None, typer.Option("--registry")] = None,
) -> None:
    """Add or refresh a repository in the Observatory registry."""

    def action() -> None:
        entry = ProjectRegistry(registry).add(_root(root), database)
        typer.echo(json.dumps(entry.to_dict(), indent=2))

    _run(action)


@observatory_app.command("list")
def observatory_list(
    registry: Annotated[Path | None, typer.Option("--registry")] = None,
) -> None:
    """List repositories registered with Athena Observatory."""
    entries = [entry.to_dict() for entry in ProjectRegistry(registry).all()]
    typer.echo(json.dumps(entries, indent=2))


@observatory_app.command("remove")
def observatory_remove(
    project_id: Annotated[str, typer.Argument(help="Project id from observatory list")],
    registry: Annotated[Path | None, typer.Option("--registry")] = None,
) -> None:
    """Remove a repository from the Observatory without deleting its Athena index."""
    if not ProjectRegistry(registry).remove(project_id):
        raise typer.BadParameter(f"Unknown Observatory project: {project_id}")
    typer.echo(f"Removed {project_id}")


@app.command()
def scan(
    root: RootOption = Path("."), json_output: Annotated[bool, typer.Option("--json")] = False
) -> None:
    """Incrementally scan a repository and derive architecture relations."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            report = runtime.scan()
        payload = {
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
        if json_output:
            typer.echo(json.dumps(payload, indent=2))
        else:
            typer.echo(
                f"Indexed {report.repository}: {report.scanned} changed, "
                f"{report.unchanged} unchanged, {report.deleted} deleted; "
                f"{report.chunks} chunks in {report.duration_ms:.2f} ms"
            )
            for warning in report.warnings:
                typer.secho(f"warning: {warning}", fg=typer.colors.YELLOW)

    _run(action)


@app.command()
def sync(root: RootOption = Path(".")) -> None:
    """Pull with rebase, push, verify the upstream, and refresh Athena's index."""

    def action() -> None:
        resolved = _root(root)
        result = sync_repository(resolved)
        with AthenaRuntime(resolved) as runtime:
            report = runtime.scan()
        typer.echo(
            f"Synchronized with {result.upstream}; indexed {report.scanned} changed, "
            f"{report.unchanged} unchanged, {report.deleted} deleted"
        )

    _run(action)


@app.command("context")
def context_command(
    task: Annotated[str, typer.Argument(help="Developer task")],
    root: RootOption = Path("."),
    persona: Annotated[str | None, typer.Option("--persona", "-p")] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="economy, eco, balanced, deep, or auto"),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    tokenizer_provider: Annotated[
        TokenizerProvider | None,
        typer.Option("--tokenizer-provider", help="generic, openai, claude, or copilot"),
    ] = None,
    target_model: Annotated[
        str | None, typer.Option("--target-model", help="Provider model used for token accounting")
    ] = None,
    allow_remote_token_counting: Annotated[
        bool | None,
        typer.Option(
            "--allow-remote-token-counting/--local-token-counting",
            help="Allow provider counting to receive the serialized context payload",
        ),
    ] = None,
    mcp_host: Annotated[
        MCPHost | None,
        typer.Option(
            "--mcp-host",
            help="Account a deterministic MCP result envelope for the selected host",
        ),
    ] = None,
) -> None:
    """Build a minimal persona-aware prompt bundle."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            bundle = runtime.context(
                task,
                persona,
                profile,
                tokenizer_provider,
                target_model,
                allow_remote_token_counting,
                mcp_host,
            )
        if json_output:
            typer.echo(bundle.to_json(pretty=True))
        else:
            typer.echo(bundle.to_prompt())
            typer.echo(
                f"\n--- Athena: persona={bundle.persona.persona_id}, "
                f"profile={bundle.profile}, estimated_tokens={bundle.estimated_tokens}, "
                f"exact_tokens={bundle.exact_tokens}, tokenizer={bundle.tokenizer}, "
                f"provider_tokens={bundle.provider_tokens}, "
                f"count_source={bundle.token_count_source}, "
                f"target_model={bundle.target_model}, hard_budget={bundle.hard_budget}, "
                f"remaining_budget={bundle.remaining_budget}, "
                f"accounting_format={bundle.accounting_format}, "
                f"accounted_bytes={bundle.accounted_bytes}, "
                f"input_ai_credits={bundle.estimated_input_ai_credits}, "
                f"confidence={bundle.retrieval_confidence:.3f} ---",
                err=True,
            )

    _run(action)


@app.command("repository-context")
def repository_context_command(
    query: Annotated[str, typer.Argument(help="Software-engineering task or context question")],
    root: RootOption = Path("."),
    persona: Annotated[str | None, typer.Option("--persona", "-p")] = None,
    continuation_token: Annotated[
        str | None, typer.Option("--continuation-token", help="Expand without repeated evidence")
    ] = None,
    request_kind: Annotated[
        Literal["context", "clarify"],
        typer.Option(
            "--request-kind",
            help="context for source evidence; clarify for metadata-only target candidates",
        ),
    ] = "context",
    json_output: Annotated[bool, typer.Option("--json/--text")] = True,
) -> None:
    """Use the same neutral economy compiler exposed through MCP."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            compiled = ContextCompiler(runtime, runtime.config.mcp.host).compile(
                query,
                persona,
                continuation_token,
                request_kind,
            )
        if json_output or request_kind == "clarify":
            typer.echo(json.dumps(compiled.payload, ensure_ascii=False, separators=(",", ":")))
        else:
            typer.echo(compiled.bundle.to_prompt())

    _run(action)


@app.command()
def graph(
    name: Annotated[str, typer.Argument(help="Symbol, path, table, or configuration key")],
    root: RootOption = Path("."),
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 50,
) -> None:
    """Inspect graph relations and evidence for a named node."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            payload = runtime.graph(name, limit)
        typer.echo(json.dumps(payload, indent=2))

    _run(action)


@app.command()
def personas(root: RootOption = Path(".")) -> None:
    """List effective built-in and repository-local personas."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            for persona in runtime.personas.all().values():
                typer.echo(
                    f"{persona.persona_id:12} {persona.policy.max_context_tokens:5} tokens  "
                    f"{persona.purpose}"
                )

    _run(action)


@app.command()
def status(root: RootOption = Path(".")) -> None:
    """Show repository index metadata and statistics."""

    def action() -> None:
        resolved = _root(root)
        with AthenaRuntime(resolved) as runtime:
            payload = runtime.status()
        current = git_head(resolved)
        payload["current_commit"] = current
        payload["stale"] = bool(
            current and payload.get("indexed_commit") not in {current, "working-tree"}
        )
        typer.echo(json.dumps(payload, indent=2))

    _run(action)


@app.command()
def diagnostics(
    root: RootOption = Path("."),
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="json or text"),
    ] = "json",
) -> None:
    """Print daemon and indexing diagnostics for IDEs and humans."""
    resolved = _root(root)
    payload = load_daemon_diagnostics(resolved)
    if format.casefold() == "json":
        typer.echo(json.dumps(payload, indent=2))
        return
    if format.casefold() != "text":
        raise typer.BadParameter("format must be json or text", param_hint="--format")
    for item in payload.get("diagnostics", []):
        path = item.get("path") or str(resolved)
        severity = item.get("severity", "warning")
        code = item.get("code", "ATHENA")
        typer.echo(f"{path}:1:1: {severity} {code}: {item.get('message', '')}")


@daemon_app.command("run")
def daemon_run(root: RootOption = Path(".")) -> None:
    """Run the watcher in the foreground."""
    resolved = _root(root)
    _run(lambda: DaemonService(resolved).run())


@daemon_app.command("start")
def daemon_start(
    root: RootOption = Path("."),
    wait_seconds: Annotated[
        float,
        typer.Option("--wait-seconds", min=0.0, max=30.0, help="Wait for daemon readiness"),
    ] = 5.0,
) -> None:
    """Start the watcher as a detached background process."""

    def action() -> None:
        resolved = _root(root)
        status_payload = ensure_daemon_running(resolved, wait_seconds)
        pid = status_payload.get("pid")
        typer.echo(
            json.dumps(
                {
                    "pid": pid,
                    "ready": bool(status_payload.get("process_alive")),
                    "state": status_payload.get("state", "starting"),
                    "status": str(resolved / ".athena" / "daemon" / "status.json"),
                },
                indent=2,
            )
        )

    _run(action)


@daemon_app.command("stop")
def daemon_stop(
    root: RootOption = Path("."),
    wait_seconds: Annotated[
        float,
        typer.Option("--wait-seconds", min=0.0, max=30.0, help="Wait for graceful shutdown"),
    ] = 5.0,
) -> None:
    """Request a graceful watcher shutdown."""
    resolved = _root(root)
    requested = request_daemon_stop(resolved)
    deadline = time.monotonic() + wait_seconds
    while requested and time.monotonic() < deadline:
        if not load_daemon_status(resolved).get("process_alive"):
            break
        time.sleep(0.05)
    payload = load_daemon_status(resolved)
    typer.echo(
        json.dumps(
            {
                "stop_requested": requested,
                "process_alive": payload.get("process_alive", False),
                "state": payload.get("state", "not-running"),
            },
            indent=2,
        )
    )


@daemon_app.command("status")
def daemon_status(root: RootOption = Path(".")) -> None:
    """Show watcher health, debounce state, and last incremental scan."""
    typer.echo(json.dumps(load_daemon_status(_root(root)), indent=2))


@app.command()
def doctor(root: RootOption = Path(".")) -> None:
    """Validate configuration, FTS5, Git, MCP installation, and workspace security."""

    def action() -> None:
        resolved = _root(root)
        config = load_config(resolved)
        semantic_plugins = SemanticPluginRegistry(config.semantic)
        envelope = host_envelope_profile(config.mcp.host)
        checks: dict[str, object] = {
            "workspace_exists": resolved.is_dir(),
            "git_available": shutil.which("git") is not None,
            "git_repository": git_head(resolved) is not None,
            "database": str(database_path(resolved, config)),
            "fts5": _has_fts5(),
            "mcp_installed": _module_available("mcp"),
            "native_watcher_installed": _module_available("watchfiles"),
            "command_execution": config.security.allow_command_execution,
            "workspace_restricted": config.security.restrict_to_workspace,
            "daemon": load_daemon_status(resolved),
            "semantic_plugins": semantic_plugins.status(),
            "mcp_envelope": {
                "host": envelope.host,
                "format": envelope.format,
                "scope": envelope.scope,
                "deterministic": envelope.deterministic,
            },
            "mcp": {
                "mode": config.mcp.mode,
                "host": config.mcp.host,
                "tools": (
                    ["repository_context"]
                    if config.mcp.mode == "economy"
                    else [
                        "athena_scan_repository",
                        "athena_build_context",
                        "athena_inspect_graph",
                        "athena_status",
                        "athena_list_personas",
                        "athena_diagnostics",
                    ]
                ),
                "profile": config.mcp.economy.profile,
                "projection": "athena-context-economy-v1",
                "representation": config.mcp.economy.response_representation,
            },
        }
        typer.echo(json.dumps(checks, indent=2))
        if not checks["fts5"]:
            raise typer.Exit(3)

    _run(action)


@app.command("generate-adapters")
def adapters(
    root: RootOption = Path("."),
    force_knowledge: Annotated[
        bool,
        typer.Option(
            "--force-knowledge",
            help="Replace installed packaged persona knowledge with the packaged version",
        ),
    ] = False,
) -> None:
    """Generate minimal Claude Code, Copilot, Cursor, and VS Code adapters."""
    resolved_root = _root(root)
    for path in install_persona_knowledge(resolved_root, overwrite=force_knowledge):
        typer.echo(str(path))
    for path in generate_adapters(resolved_root):
        typer.echo(str(path))


@app.command()
def metrics(
    root: RootOption = Path("."),
    limit: Annotated[int, typer.Option("--limit", min=1, max=200)] = 20,
) -> None:
    """Show local scan and context construction measurements."""

    def action() -> None:
        with AthenaRuntime(_root(root)) as runtime:
            repository = runtime.status().get("repository")
            payload = runtime.store.metrics_summary(str(repository), limit)
        typer.echo(json.dumps(payload, indent=2))

    _run(action)


@app.command("export-graph")
def export_graph_command(
    destination: Annotated[Path, typer.Argument(help="Output file")],
    root: RootOption = Path("."),
    format: Annotated[
        str, typer.Option("--format", "-f", help="json, graphml, or mermaid")
    ] = "json",
) -> None:
    """Export the complete code and persona graph."""

    def action() -> None:
        normalized = format.casefold()
        if normalized not in {"json", "graphml", "mermaid"}:
            raise AthenaError(f"Unsupported export format: {format}")
        with AthenaRuntime(_root(root)) as runtime:
            output = export_graph(runtime.store, destination.expanduser().resolve(), normalized)
        typer.echo(str(output))

    _run(action)


@app.command("eval")
def evaluate(
    dataset: Annotated[Path, typer.Argument(help="YAML or JSON evaluation dataset")],
    root: RootOption = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Measure routing, retrieval quality, latency, and estimated context size."""

    def action() -> None:
        report = run_evaluation(_root(root), load_cases(dataset.expanduser().resolve()))
        if json_output:
            typer.echo(json.dumps(report, indent=2))
            return
        summary = report["summary"]
        typer.echo("=== Athena evaluation ===")
        for key, value in summary.items():
            typer.echo(f"{key:24}: {value}")
        typer.echo("\nCases:")
        for case in report["cases"]:
            typer.echo(
                f"- {case['id']}: persona={case['persona']} "
                f"P={case['precision']} R={case['recall']} "
                f"MRR={case['reciprocal_rank']} tokens={case['estimated_tokens']}"
            )

    _run(action)


@app.command()
def benchmark(
    dataset: Annotated[Path, typer.Argument(help="Versioned YAML or JSON evaluation dataset")],
    root: RootOption = Path("."),
    scan_index: Annotated[
        bool, typer.Option("--scan", help="Scan the repository before benchmarking")
    ] = False,
    gate: Annotated[
        bool, typer.Option("--gate/--no-gate", help="Fail when a configured threshold is missed")
    ] = False,
    mode: Annotated[
        Literal["full", "economy"],
        typer.Option("--mode", help="Benchmark the full or one-tool economy context path"),
    ] = "full",
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write the JSON report")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Benchmark cold/warm retrieval, quality, and configured release gates."""

    def action() -> None:
        loaded = load_dataset(dataset.expanduser().resolve())
        report = run_benchmark(_root(root), loaded, scan=scan_index, mode=mode)
        rendered = json.dumps(report, indent=2)
        if output is not None:
            destination = output.expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered + "\n", encoding="utf-8")
        if json_output:
            typer.echo(rendered)
        else:
            typer.echo(f"=== Athena benchmark: {report['dataset']} ===")
            for key, value in report["summary"].items():
                typer.echo(f"{key:28}: {value}")
            typer.echo("\nLatency:")
            for name, values in report["latency"].items():
                typer.echo(
                    f"{name:28}: p50={values['p50_ms']:.3f} ms "
                    f"p95={values['p95_ms']:.3f} ms p99={values['p99_ms']:.3f} ms"
                )
            gate_result = report["gate"]
            typer.echo(f"\nRelease gate: {'PASS' if gate_result['passed'] else 'FAIL'}")
            for failure in gate_result["failures"]:
                typer.echo(f"- {failure}")
        if gate and not report["gate"]["passed"]:
            raise typer.Exit(1)

    _run(action)


@app.command("evaluation-schema")
def write_evaluation_schema(
    destination: Annotated[Path, typer.Argument(help="Destination JSON Schema file")],
) -> None:
    """Write the supported versioned evaluation-dataset JSON Schema."""
    output = destination.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evaluation_schema(), indent=2) + "\n", encoding="utf-8")
    typer.echo(str(output))


@app.command()
def mcp(
    root: RootOption = Path("."),
    mode: Annotated[
        Literal["full", "economy"] | None,
        typer.Option(
            "--mode",
            help="full exposes diagnostics tools; economy exposes one compact context tool",
        ),
    ] = None,
    copilot: Annotated[
        bool,
        typer.Option(
            "--copilot",
            help="Expose one auto-refreshing, token-frugal context tool for Copilot Agent mode",
        ),
    ] = False,
    daemon: Annotated[
        bool,
        typer.Option(
            "--daemon/--no-daemon",
            help="Ensure the persistent watcher is running before starting MCP",
        ),
    ] = False,
    mcp_host: Annotated[
        MCPHost | None,
        typer.Option(
            "--mcp-host",
            help="generic-mcp, vscode-copilot, jetbrains-copilot, claude-code, or codex",
        ),
    ] = None,
) -> None:
    """Start the official MCP stdio server."""
    from athena.mcp import run_server

    run_server(_root(root), copilot, daemon, mcp_host, mode)


def _has_fts5() -> bool:
    db = sqlite3.connect(":memory:")
    try:
        db.execute("CREATE VIRTUAL TABLE probe USING fts5(value)")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        db.close()


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    app()
