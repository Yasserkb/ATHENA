from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from athena.cache import BoundedCache
from athena.config import AppConfig, database_path, load_config
from athena.context_projection import ProjectionId, ResponseRepresentation
from athena.domain import ContextBundle, IndexedFileAnalysis, Persona, ScanReport
from athena.indexing import RepositoryScanner
from athena.indexing.scanner import repository_identity
from athena.indexing.semantic import SemanticPluginRegistry
from athena.mcp_envelope import MCPHost
from athena.personas import PersonaRegistry, PersonaRouter
from athena.personas.graph import write_persona_graph
from athena.retrieval import RetrievalRequestKind, RetrievalService, apply_profile, resolve_profile
from athena.security import WorkspaceGuard
from athena.storage import SQLiteStore
from athena.tokenization import TokenizerProvider


class AthenaRuntime:
    def __init__(self, root: Path) -> None:
        self.guard = WorkspaceGuard(root)
        self.root = self.guard.root
        self.config: AppConfig = load_config(self.root)
        self.store = SQLiteStore(
            database_path(self.root, self.config), self.config.retrieval.cache_max_entries
        )
        self.personas = PersonaRegistry(self.root, self.config.personas.extra_dirs)
        self.router = PersonaRouter()
        self.analysis_cache: BoundedCache[tuple[object, ...], IndexedFileAnalysis] = BoundedCache(
            self.config.retrieval.cache_max_entries
        )
        self.retrieval = RetrievalService(self.store, self.config)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> AthenaRuntime:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def scan(self) -> ScanReport:
        report = RepositoryScanner(self.root, self.config, self.store, self.analysis_cache).scan()
        write_persona_graph(self.store, self.personas.all())
        totals = self.store.stats()
        return ScanReport(
            report.repository,
            report.scanned,
            report.unchanged,
            report.deleted,
            totals["chunks"],
            totals["nodes"],
            totals["edges"],
            report.duration_ms,
            report.warnings,
        )

    def context(
        self,
        task: str,
        persona_id: str | None = None,
        profile: str | None = None,
        tokenizer_provider: TokenizerProvider | None = None,
        target_model: str | None = None,
        allow_remote_token_counting: bool | None = None,
        mcp_host: MCPHost | None = None,
        projection_id: ProjectionId = "full-v1",
        response_representation: ResponseRepresentation = "structured-compat-v1",
        continuation_token: str | None = None,
        excluded_chunk_ids: frozenset[str] = frozenset(),
        max_context_tokens: int | None = None,
        incremental_files_scanned: int = 0,
        request_kind: RetrievalRequestKind = "context",
        clarification_max_candidates: int = 3,
        clarification_confidence_threshold: float = 0.72,
        clarification_margin_threshold: float = 0.12,
    ) -> ContextBundle:
        all_personas = self.personas.all()
        if persona_id:
            persona = self.personas.get(persona_id)
            route_confidence = 1.0
        else:
            persona, route_confidence = self.router.route(task, all_personas)
        effective_provider = tokenizer_provider or self.config.tokenization.provider
        requested_profile = (
            "copilot-economy" if effective_provider == "copilot" and profile is None else profile
        )
        profile_name = resolve_profile(task, requested_profile)
        persona = apply_profile(persona, profile_name)
        if max_context_tokens is not None:
            persona = replace(
                persona,
                policy=replace(persona.policy, max_context_tokens=max_context_tokens),
            )
        repository_name, _ = repository_identity(self.root)
        return self.retrieval.build_bundle(
            task,
            persona,
            repository_name,
            route_confidence,
            profile_name,
            tokenizer_provider,
            target_model,
            allow_remote_token_counting,
            mcp_host,
            projection_id,
            response_representation,
            continuation_token,
            excluded_chunk_ids,
            incremental_files_scanned,
            request_kind,
            clarification_max_candidates,
            clarification_confidence_threshold,
            clarification_margin_threshold,
        )

    def graph(self, name: str, limit: int = 50) -> list[dict[str, object]]:
        return self.store.node_neighbors(name, limit)

    def clear_retrieval_caches(self) -> None:
        self.store.clear_caches()
        self.retrieval.clear_caches()

    def persona(self, persona_id: str) -> Persona:
        return self.personas.get(persona_id)

    def status(self) -> dict[str, object]:
        from athena.daemon import load_daemon_diagnostics, load_daemon_status

        metadata = self.store.metadata()
        diagnostics = load_daemon_diagnostics(self.root)
        return {
            "root": str(self.root),
            "database": str(self.store.path),
            "repository": metadata.get("repository_name", self.root.name),
            "repository_id": metadata.get("repository_id"),
            "indexed_commit": metadata.get("indexed_commit"),
            "last_scan_epoch": metadata.get("last_scan_epoch"),
            "schema_version": metadata.get("schema_version"),
            "index_generation": self.store.index_generation(),
            "index_degraded": metadata.get("index_degraded") == "true",
            "failed_paths": json.loads(metadata.get("failed_paths", "[]")),
            "stats": self.store.stats(),
            "personas": sorted(self.personas.all()),
            "caches": {
                **self.store.cache_status(),
                **self.retrieval.cache_status(),
                "parsed_files": self.analysis_cache.stats().to_dict(),
            },
            "security": {
                "restrict_to_workspace": self.config.security.restrict_to_workspace,
                "allow_command_execution": self.config.security.allow_command_execution,
                "redact_secrets": self.config.security.redact_secrets,
            },
            "tokenization": self.config.tokenization.model_dump(mode="json"),
            "mcp": self.config.mcp.model_dump(mode="json"),
            "semantic_plugins": SemanticPluginRegistry(self.config.semantic).status(),
            "daemon": load_daemon_status(self.root),
            "diagnostics": diagnostics.get("summary", {}),
        }
