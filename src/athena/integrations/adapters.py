from __future__ import annotations

import json
from pathlib import Path

_CANONICAL = """# Athena CodeGraph

Use Athena as the repository context layer. Do not load the complete Athena framework into the
conversation.

For repository work:
1. In economy mode, call `repository_context` once before broad exploration.
2. Reuse its paths, line ranges, relationships, and evidence.
3. Use its continuation token only when the first result is insufficient.
4. Verify exact source before editing when confidence is low.
5. Skip Athena for general questions and trivial edits in an already-provided file.
"""

_COPILOT = """# Athena dynamic repository context

For repository questions that require understanding or changing code, call `athena_context` exactly
once before opening files. Use its ranked evidence as the starting context. Do not repeat searches
or reopen the same files unless Athena reports low confidence or missing evidence. Keep responses
concise and stop after the requested change and verification. Do not call Athena for general
questions that do not require repository context.

When the user explicitly names a persona, pass that persona to `athena_context`. Otherwise allow
Athena's normal task router to choose. Do not silently switch to a specialized persona merely
because one is installed.
"""


def generate_adapters(root: Path) -> list[Path]:
    resolved = root.resolve()
    codex_root = resolved.as_posix()
    outputs = {
        root / "AGENTS.md": _CANONICAL
        + "\nClaude Code: use the configured Athena MCP tools directly.\n",
        root / ".github" / "copilot-instructions.md": _COPILOT,
        root / ".cursor" / "rules" / "athena.mdc": (
            "---\ndescription: Athena local code graph\nalwaysApply: true\n---\n\n" + _CANONICAL
        ),
        root / ".vscode" / "mcp.json": json.dumps(
            {
                "servers": {
                    "athena": {
                        "type": "stdio",
                        "command": "athena",
                        "args": [
                            "mcp",
                            "--root",
                            "${workspaceFolder}",
                            "--copilot",
                            "--daemon",
                            "--mcp-host",
                            "vscode-copilot",
                        ],
                    }
                }
            },
            indent=2,
        )
        + "\n",
        root / ".athena" / "jetbrains-copilot-mcp.json": json.dumps(
            {
                "servers": {
                    "athena": {
                        "type": "stdio",
                        "command": "athena",
                        "args": [
                            "mcp",
                            "--root",
                            str(root.resolve()),
                            "--copilot",
                            "--daemon",
                            "--mcp-host",
                            "jetbrains-copilot",
                        ],
                    }
                }
            },
            indent=2,
        )
        + "\n",
        root / ".athena" / "codex-mcp-config.toml": (
            "# Review and merge this block into .codex/config.toml.\n"
            "# Athena never overwrites existing Codex project configuration.\n\n"
            "[mcp_servers.athena]\n"
            'command = "athena"\n'
            f'args = ["mcp", "--root", "{codex_root}", "--mode", "economy", '
            '"--mcp-host", "codex", "--daemon"]\n'
            f'cwd = "{codex_root}"\n'
            "enabled = true\n"
            'enabled_tools = ["repository_context"]\n'
            'default_tools_approval_mode = "approve"\n'
            "startup_timeout_sec = 20\n"
            "tool_timeout_sec = 60\n"
        ),
    }
    written: list[Path] = []
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written
