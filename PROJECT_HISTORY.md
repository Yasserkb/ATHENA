# Athena CodeGraph implementation history

This repository was imported into Git after the initial implementation work.
The Git commits organize the final source snapshot by subsystem; they do not
represent the original chronological development timestamps.

## Repository intelligence

- Added local-first source indexing backed by SQLite and FTS5.
- Added structural parsing and architecture graph derivation.
- Added exact-symbol, lexical, and graph-assisted retrieval.
- Added incremental scanning and index-generation tracking.
- Added secret redaction and workspace-boundary enforcement.

## Context and token budgeting

- Added persona-aware context compilation.
- Added economy-mode context projection.
- Added provider-aware token accounting.
- Added deterministic MCP envelope accounting.
- Added bounded continuation tokens for expanding context.
- Added bounded ambiguity clarification with metadata-only candidates, deterministic confidence
  checks, separate token limits, and isolated metrics.

## Personas

- Added architect, developer, reviewer, debugger, release, testing, security,
  backend, frontend, data, cloud, mobile, Python, TypeScript, Spring/Angular,
  MERN, T3, T4, and other specialist personas.
- Added packaged persona knowledge and repository-local installation.
- Improved specialist routing above the generic developer fallback.
- Bounded persona prompt cards to preserve context budgets.

## MCP and integrations

- Added official MCP STDIO support.
- Added one-tool economy mode exposing repository_context.
- Added Codex, Claude Code, Copilot, Cursor, VS Code, and JetBrains adapters.
- Added host-specific MCP envelope accounting.
- Kept MCP local-first with no arbitrary command-execution tool.

## Persistent daemon

- Added native filesystem watching with polling fallback.
- Added atomic daemon status, diagnostics, PID, and heartbeat files.
- Added stale PID detection and daemon-process ownership validation.
- Added protection against PID reuse across container restarts.
- Added immediate scanning status during startup.
- Added graceful native-watcher fallback for read-only repositories.
- Added ignored-directory pruning to reduce Windows and Docker filesystem load.

## Docker and runtime state

- Separated the read-only repository from writable SQLite and daemon state with
  ATHENA_STATE_DIR.
- Added a non-root, read-only, capability-dropped Docker runtime.
- Added persistent /data state volume support.
- Changed Docker Compose to run the watcher as its foreground service.
- Added daemon-aware health checks.
- Added native-venv operation so Docker Desktop is optional.

## Validation

- Added automated coverage for storage, indexing, retrieval, personas,
  tokenization, semantic plugins, MCP, daemon lifecycle, stale PID recovery,
  container state separation, and security.
- Verified the complete suite after the daemon and scanner fixes.
