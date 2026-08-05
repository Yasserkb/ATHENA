from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from athena.context_projection import ResponseRepresentation
from athena.errors import ConfigurationError
from athena.mcp_envelope import MCPHost
from athena.tokenization import TokenizerProvider


class IndexConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database: str = ".athena/index.db"
    max_file_bytes: int = Field(default=1_000_000, ge=1_024)
    chunk_lines: int = Field(default=80, ge=20, le=400)
    chunk_overlap_lines: int = Field(default=12, ge=0, le=100)
    parse_workers: int = Field(default=0, ge=0, le=32)
    write_batch_size: int = Field(default=100, ge=1, le=1000)
    include_extensions: list[str] = Field(
        default_factory=lambda: [
            ".java",
            ".kt",
            ".kts",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".mjs",
            ".cjs",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".c",
            ".h",
            ".cc",
            ".cpp",
            ".cxx",
            ".hpp",
            ".swift",
            ".dart",
            ".yaml",
            ".yml",
            ".properties",
            ".sql",
            ".md",
        ]
    )
    exclude_globs: list[str] = Field(
        default_factory=lambda: [
            "**/.git/**",
            "**/target/**",
            "**/build/**",
            "**/node_modules/**",
            "**/.venv/**",
            "**/__pycache__/**",
        ]
    )
    secret_scan: bool = True


class RetrievalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_k_lexical: int = Field(default=20, ge=1, le=100)
    top_k_exact: int = Field(default=12, ge=1, le=100)
    graph_depth: int = Field(default=2, ge=0, le=5)
    graph_max_nodes: int = Field(default=40, ge=1, le=500)
    min_score: float = Field(default=0.05, ge=0.0, le=1.0)
    cache_max_entries: int = Field(default=256, ge=0, le=10_000)
    bundle_cache_entries: int = Field(default=64, ge=0, le=1_000)
    token_cache_entries: int = Field(default=4_096, ge=0, le=100_000)


class TokenizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["generic", "openai", "claude", "copilot"] = "generic"
    target_model: str | None = None
    openai_encoding: str = "o200k_base"
    claude_remote_counting: bool = False
    anthropic_api_key_env: str = "ANTHROPIC_API_KEY"
    copilot_model_provider: Literal["auto", "generic", "openai", "claude"] = "auto"
    copilot_input_usd_per_million: float | None = Field(default=None, gt=0)
    copilot_monthly_ai_credits: int = Field(default=6_000, ge=1)


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    restrict_to_workspace: bool = True
    allow_command_execution: bool = False
    redact_secrets: bool = True


class PersonasConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    extra_dirs: list[str] = Field(default_factory=lambda: [".athena/personas"])


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    store_task_text: bool = False


class DaemonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    poll_interval_ms: int = Field(default=250, ge=50, le=60_000)
    debounce_ms: int = Field(default=500, ge=50, le=60_000)
    max_batch_delay_ms: int = Field(default=2_000, ge=100, le=300_000)
    heartbeat_timeout_seconds: int = Field(default=10, ge=2, le=300)


class SemanticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    load_entry_points: bool = True
    enabled_plugins: list[str] = Field(default_factory=list)
    disabled_plugins: list[str] = Field(default_factory=list)


class EconomyMcpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: str = "economy"
    tokenizer_provider: TokenizerProvider = "openai"
    target_model: str | None = None
    response_representation: ResponseRepresentation = "compact-text-v1"
    max_context_tokens: int = Field(default=1400, ge=400, le=7000)
    clarification_max_tokens: int = Field(default=400, ge=200, le=1200)
    clarification_max_candidates: int = Field(default=3, ge=1, le=5)
    clarification_confidence_threshold: float = Field(default=0.72, ge=0.0, le=1.0)
    clarification_margin_threshold: float = Field(default=0.12, ge=0.0, le=1.0)
    continuation_ttl_minutes: int = Field(default=45, ge=1, le=240)


class McpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: MCPHost = "generic-mcp"
    mode: Literal["full", "economy"] = "full"
    economy: EconomyMcpConfig = Field(default_factory=EconomyMcpConfig)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    index: IndexConfig = Field(default_factory=IndexConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    tokenization: TokenizationConfig = Field(default_factory=TokenizationConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    personas: PersonasConfig = Field(default_factory=PersonasConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)

    @property
    def supported_schema_version(self) -> int:
        return 1


def locate_config(root: Path) -> Path | None:
    candidate = root / ".athena" / "config.yaml"
    return candidate if candidate.is_file() else None


def load_config(root: Path) -> AppConfig:
    path = locate_config(root)
    if path is None:
        return AppConfig()
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        config = AppConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigurationError(f"Invalid Athena configuration at {path}: {exc}") from exc
    if config.schema_version != config.supported_schema_version:
        raise ConfigurationError(
            f"Unsupported configuration schema {config.schema_version}; "
            f"runtime supports {config.supported_schema_version}"
        )
    return config


def database_path(root: Path, config: AppConfig) -> Path:
    state = state_directory()
    if state is not None:
        return state / "index.db"
    path = Path(config.index.database).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def state_directory() -> Path | None:
    """Return the optional external runtime-state directory.

    Containers use this to keep the repository mount read-only while SQLite and daemon
    coordination files live on a dedicated writable volume.
    """
    configured = os.getenv("ATHENA_STATE_DIR", "").strip()
    if not configured:
        return None
    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise ConfigurationError("ATHENA_STATE_DIR must be an absolute path")
    return path.resolve()
