from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field, replace

from athena.cache import BoundedCache
from athena.config import AppConfig
from athena.context_projection import (
    FULL_PROJECTION,
    ProjectionId,
    ResponseRepresentation,
    projection_json,
    serialize_projected_result,
)
from athena.domain import Chunk, ContextBundle, Persona, RetrievalHit
from athena.errors import TokenBudgetError
from athena.indexing.common import exact_search_terms
from athena.mcp_envelope import MCPHost, host_envelope_profile
from athena.storage import SQLiteStore
from athena.tokenization import (
    TokenCount,
    TokenCounter,
    TokenizerProvider,
    create_token_counter,
    estimate_tokens,
)


@dataclass(slots=True)
class _Candidate:
    chunk: Chunk
    scores: list[float] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    graph_distance: int | None = None

    @property
    def score(self) -> float:
        # Probabilistic OR rewards agreement between independent retrieval channels.
        miss_probability = 1.0
        for value in self.scores:
            miss_probability *= 1.0 - max(0.0, min(0.99, value))
        return 1.0 - miss_probability


class RetrievalService:
    def __init__(self, store: SQLiteStore, config: AppConfig) -> None:
        self.store = store
        self.config = config
        self._observed_generation = store.index_generation()
        self._bundle_cache: BoundedCache[tuple[object, ...], ContextBundle] = BoundedCache(
            config.retrieval.bundle_cache_entries
        )
        self._persona_card_cache: BoundedCache[Persona, str] = BoundedCache(128)
        self._token_cache: BoundedCache[tuple[str, str], int] = BoundedCache(
            config.retrieval.token_cache_entries
        )
        self._provider_token_cache: BoundedCache[tuple[str, str], TokenCount] = BoundedCache(
            config.retrieval.token_cache_entries
        )

    def build_bundle(
        self,
        task: str,
        persona: Persona,
        repository: str,
        route_confidence: float,
        profile: str = "balanced",
        tokenizer_provider: TokenizerProvider | None = None,
        target_model: str | None = None,
        allow_remote_token_counting: bool | None = None,
        mcp_host: MCPHost | None = None,
        projection_id: ProjectionId = FULL_PROJECTION,
        response_representation: ResponseRepresentation = "structured-compat-v1",
        continuation_token: str | None = None,
        excluded_chunk_ids: frozenset[str] = frozenset(),
        incremental_files_scanned: int = 0,
    ) -> ContextBundle:
        started = time.perf_counter()
        provider = tokenizer_provider or self.config.tokenization.provider
        model = target_model or self.config.tokenization.target_model
        allow_remote = (
            self.config.tokenization.claude_remote_counting
            if allow_remote_token_counting is None
            else allow_remote_token_counting
        )
        counter = create_token_counter(
            provider,
            model,
            self.config.tokenization.openai_encoding,
            allow_remote,
            self.config.tokenization.anthropic_api_key_env,
            self.config.tokenization.copilot_model_provider,
        )
        generation = self.store.index_generation()
        if generation != self._observed_generation:
            self._bundle_cache.invalidate()
            self._observed_generation = generation
        cache_key = (
            generation,
            repository,
            task,
            persona,
            route_confidence,
            profile,
            repr(self.config.retrieval.model_dump(mode="json")),
            repr(self.config.tokenization.model_dump(mode="json")),
            provider,
            model,
            counter.tokenizer,
            allow_remote,
            mcp_host,
            projection_id,
            response_representation,
            continuation_token,
            tuple(sorted(excluded_chunk_ids)),
            incremental_files_scanned,
        )
        cached = self._bundle_cache.get(cache_key)
        if cached is not None:
            duration_ms = (time.perf_counter() - started) * 1000
            self.store.record_metric(
                "context",
                repository,
                duration_ms,
                cached.provider_tokens or cached.estimated_tokens,
                len(cached.hits),
                {
                    "persona": persona.persona_id,
                    "confidence": cached.retrieval_confidence,
                    "cache_hit": True,
                    "index_generation": generation,
                    "tokenizer": cached.tokenizer,
                    "target_model": cached.target_model,
                    "exact_token_count": cached.exact_tokens is not None,
                    "provider_tokens": cached.provider_tokens,
                    "token_count_source": cached.token_count_source,
                    "mcp_host": cached.mcp_host,
                    "accounting_format": cached.accounting_format,
                    "accounting_scope": cached.accounting_scope,
                    "accounted_bytes": cached.accounted_bytes,
                    "estimated_input_ai_credits": cached.estimated_input_ai_credits,
                    "monthly_ai_credit_budget": cached.monthly_ai_credit_budget,
                },
            )
            return cached
        terms = exact_search_terms(task)
        exact_candidates = [
            (node, score)
            for node, score in self.store.exact_nodes(terms, self.config.retrieval.top_k_exact * 2)
            if node.path != "@persona"
        ]
        # Personas constrain the graph's starting point. If the requested kinds do not
        # match, retain the unfiltered list as a graceful fallback rather than returning
        # no context for a legitimate but unfamiliar language/framework symbol.
        preferred_kinds = set(persona.policy.start_kinds)
        scoped_exact = [item for item in exact_candidates if item[0].kind in preferred_kinds]
        exact = (scoped_exact or exact_candidates)[: self.config.retrieval.top_k_exact]
        seed_ids = [node.node_id for node, _ in exact]
        candidates: dict[str, _Candidate] = {}

        # Exact node/path/config matches are the strongest source-code signal.
        exact_chunks = self.store.chunks_for_nodes(seed_ids, limit=100)
        exact_scores = {node.node_id: score for node, score in exact}
        for chunk in exact_chunks:
            base = exact_scores.get(chunk.symbol_id or "", 0.72)
            self._add(candidates, chunk, min(0.97, base), "exact-symbol")

        # Unicode FTS5/BM25 handles identifiers and natural-language terms without a model.
        lexical = self.store.lexical_chunks(task, self.config.retrieval.top_k_lexical)
        for rank, (chunk, bm25_score) in enumerate(lexical, 1):
            reciprocal = 1.0 / math.sqrt(rank)
            score = min(0.88, 0.35 + 0.35 * reciprocal + 0.25 * bm25_score)
            self._add(candidates, chunk, score, f"fts-rank-{rank}")

        graph_depth = min(persona.policy.graph_depth, self.config.retrieval.graph_depth)
        graph = self.store.graph_walk(
            seed_ids,
            persona.policy.traverse_relations,
            graph_depth,
            self.config.retrieval.graph_max_nodes,
        )
        graph_ids = [node.node_id for node, _, _ in graph]
        graph_distance = {node.node_id: distance for node, distance, _ in graph}
        relation_for = {node.node_id: relation for node, _, relation in graph}
        for chunk in self.store.chunks_for_nodes(graph_ids, limit=160):
            distance = graph_distance.get(chunk.symbol_id or "", 2)
            score = 0.64 / max(1, distance)
            self._add(
                candidates,
                chunk,
                score,
                f"graph:{relation_for.get(chunk.symbol_id or '', 'related')}",
                distance,
            )

        requested_tags = _requested_tags(task)
        persona_tags = set(persona.policy.include_tags)
        for candidate in candidates.values():
            matching = requested_tags.intersection(candidate.chunk.tags)
            if matching:
                candidate.scores.append(0.48)
                candidate.reasons.append("task-tag:" + ",".join(sorted(matching)))
            persona_matching = persona_tags.intersection(candidate.chunk.tags)
            if persona_matching:
                candidate.scores.append(0.20)
                candidate.reasons.append("persona-tag:" + ",".join(sorted(persona_matching)))

        ranked = sorted(candidates.values(), key=lambda x: x.score, reverse=True)
        dynamic_threshold = self.config.retrieval.min_score
        if ranked:
            dynamic_threshold = max(dynamic_threshold, min(0.45, ranked[0].score * 0.40))
        ranked = [
            x
            for x in ranked
            if x.score >= dynamic_threshold and x.chunk.chunk_id not in excluded_chunk_ids
        ]
        selected = self._pack(ranked, persona)
        selected = self._apply_evidence_levels(selected)
        hits = tuple(
            RetrievalHit(
                candidate.chunk,
                round(candidate.score, 6),
                tuple(dict.fromkeys(candidate.reasons)),
                candidate.graph_distance,
            )
            for candidate in selected
        )
        architecture_ids = list(dict.fromkeys([*seed_ids, *graph_ids]))
        architecture = tuple(self.store.architecture_lines(architecture_ids, limit=24))
        warnings: list[str] = []
        if not exact:
            warnings.append(
                "No exact symbol, path, endpoint, table, or configuration-key match was found."
            )
        if not hits:
            warnings.append(
                "No indexed evidence met the retrieval threshold; inspect or rescan the repository."
            )
        if hits and hits[0].score < 0.6:
            warnings.append("Retrieval confidence is low; verify source files before editing.")
        if "test" in requested_tags and not any("test" in hit.chunk.tags for hit in hits):
            warnings.append("The task mentions tests, but no related test evidence was retrieved.")
        top_score = hits[0].score if hits else 0.0
        confidence = round(min(1.0, 0.25 * route_confidence + 0.75 * top_score), 3)
        bundle = self._enforce_payload_budget(
            repository,
            task,
            persona,
            hits,
            architecture,
            confidence,
            warnings,
            profile,
            counter,
            (
                self.config.tokenization.copilot_input_usd_per_million
                if provider == "copilot"
                else None
            ),
            (
                self.config.tokenization.copilot_monthly_ai_credits
                if provider == "copilot"
                else None
            ),
            mcp_host,
            projection_id,
            response_representation,
            continuation_token,
            incremental_files_scanned,
        )
        duration_ms = (time.perf_counter() - started) * 1000
        self.store.record_metric(
            "context",
            repository,
            duration_ms,
            bundle.provider_tokens or bundle.estimated_tokens,
            len(bundle.hits),
            {
                "persona": persona.persona_id,
                "exact_nodes": len(exact),
                "lexical_hits": len(lexical),
                "graph_nodes": len(graph),
                "confidence": confidence,
                "cache_hit": False,
                "index_generation": generation,
                "tokenizer": bundle.tokenizer,
                "target_model": bundle.target_model,
                "exact_token_count": bundle.exact_tokens is not None,
                "provider_tokens": bundle.provider_tokens,
                "token_count_source": bundle.token_count_source,
                "hard_budget": bundle.hard_budget,
                "remaining_budget": bundle.remaining_budget,
                "serialized_bytes": bundle.serialized_bytes,
                "accounted_bytes": bundle.accounted_bytes,
                "mcp_host": bundle.mcp_host,
                "accounting_format": bundle.accounting_format,
                "accounting_scope": bundle.accounting_scope,
                "host_envelope_overhead_estimated_tokens": (
                    bundle.host_envelope_overhead_estimated_tokens
                ),
                "dropped_evidence": bundle.dropped_evidence,
                "estimated_input_ai_credits": bundle.estimated_input_ai_credits,
                "monthly_ai_credit_budget": bundle.monthly_ai_credit_budget,
                "projection_id": bundle.projection_id,
                "response_representation": bundle.response_representation,
                "continuation": bool(bundle.continuation_token),
                "incremental_files_scanned": bundle.incremental_files_scanned,
            },
        )
        self._bundle_cache.put(cache_key, bundle, duration_ms)
        return bundle

    def cache_status(self) -> dict[str, dict[str, int | float]]:
        return {
            "context_bundles": self._bundle_cache.stats().to_dict(),
            "persona_cards": self._persona_card_cache.stats().to_dict(),
            "token_counts": self._token_cache.stats().to_dict(),
            "provider_token_counts": self._provider_token_cache.stats().to_dict(),
        }

    def clear_caches(self) -> None:
        self._bundle_cache.invalidate()
        self._persona_card_cache.invalidate()
        self._token_cache.invalidate()
        self._provider_token_cache.invalidate()

    @staticmethod
    def _add(
        candidates: dict[str, _Candidate],
        chunk: Chunk,
        score: float,
        reason: str,
        graph_distance: int | None = None,
    ) -> None:
        candidate = candidates.setdefault(chunk.chunk_id, _Candidate(chunk))
        candidate.scores.append(score)
        candidate.reasons.append(reason)
        if graph_distance is not None:
            if candidate.graph_distance is None:
                candidate.graph_distance = graph_distance
            else:
                candidate.graph_distance = min(candidate.graph_distance, graph_distance)

    def _pack(self, ranked: list[_Candidate], persona: Persona) -> list[_Candidate]:
        budget = persona.policy.max_context_tokens
        persona_card = self._persona_card_cache.get_or_compute(persona, persona.prompt_card)
        used = self._estimate_tokens(persona_card)
        per_file: dict[str, int] = defaultdict(int)
        selected: list[_Candidate] = []
        for candidate in ranked:
            if per_file[candidate.chunk.path] >= persona.policy.max_chunks_per_file:
                continue
            if any(
                _overlap_ratio(candidate.chunk, existing.chunk) >= 0.55 for existing in selected
            ):
                continue
            cost = self._estimate_tokens(candidate.chunk.content) + 25
            if selected and used + cost > budget:
                continue
            if not selected and cost > budget - used:
                truncated = _truncate_chunk(candidate.chunk, max(100, budget - used - 25))
                candidate = _Candidate(
                    truncated,
                    candidate.scores,
                    [*candidate.reasons, "truncated-to-budget"],
                    candidate.graph_distance,
                )
                cost = self._estimate_tokens(truncated.content) + 25
            selected.append(candidate)
            per_file[candidate.chunk.path] += 1
            used += cost
            if used >= budget:
                break
        return selected

    @staticmethod
    def _apply_evidence_levels(selected: list[_Candidate]) -> list[_Candidate]:
        """Keep the primary target intact and compact secondary source evidence.

        This is deliberately source-preserving: compact evidence is a leading exact
        range from the selected chunk, rather than an invented summary. The caller can
        still inspect the full indexed range through graph/context tooling when needed.
        """
        represented: list[_Candidate] = []
        for index, candidate in enumerate(selected):
            if index == 0 or candidate.chunk.language in {"yaml", "properties", "sql"}:
                represented.append(candidate)
                continue
            compact = _compact_source_chunk(candidate.chunk, max_lines=14)
            represented.append(
                _Candidate(
                    compact,
                    candidate.scores,
                    [*candidate.reasons, "compressed-secondary-evidence"],
                    candidate.graph_distance,
                )
            )
        return represented

    def _enforce_payload_budget(
        self,
        repository: str,
        task: str,
        persona: Persona,
        hits: tuple[RetrievalHit, ...],
        architecture: tuple[str, ...],
        retrieval_confidence: float,
        warnings: list[str],
        profile: str,
        counter: TokenCounter,
        input_usd_per_million: float | None,
        monthly_ai_credits: int | None,
        mcp_host: MCPHost | None,
        projection_id: ProjectionId,
        response_representation: ResponseRepresentation,
        continuation_token: str | None,
        incremental_files_scanned: int,
    ) -> ContextBundle:
        kept = list(hits)
        kept_architecture = list(architecture)
        effective_task = task
        dropped_evidence = 0
        architecture_dropped = False
        task_truncated = False
        budget = persona.policy.max_context_tokens
        while True:
            effective_warnings = list(warnings)
            if dropped_evidence:
                effective_warnings.append(
                    f"Dropped {dropped_evidence} evidence item(s) to satisfy the hard "
                    "serialized payload budget."
                )
            if architecture_dropped:
                effective_warnings.append(
                    "Architecture lines were removed to satisfy the hard serialized payload budget."
                )
            if task_truncated:
                effective_warnings.append(
                    "Task text was truncated to satisfy the hard serialized payload budget."
                )
            base = ContextBundle(
                repository,
                effective_task,
                persona,
                tuple(kept),
                tuple(kept_architecture),
                0,
                retrieval_confidence,
                tuple(effective_warnings),
                profile,
                projection_id=projection_id,
                response_representation=response_representation,
                continuation_token=continuation_token,
                incremental_files_scanned=incremental_files_scanned,
            )
            bundle = self._account_payload(
                base,
                counter,
                budget,
                dropped_evidence,
                input_usd_per_million,
                monthly_ai_credits,
                mcp_host,
            )
            used = bundle.provider_tokens or bundle.estimated_tokens
            if used <= budget:
                return bundle
            if kept:
                kept.pop()
                dropped_evidence += 1
                continue
            if kept_architecture:
                kept_architecture.pop()
                architecture_dropped = True
                continue
            if effective_task:
                overflow = used - budget
                retained = max(0, len(effective_task) - max(32, overflow * 4))
                shortened = effective_task[:retained].rstrip()
                effective_task = (
                    shortened + "\n...[Athena: task truncated to payload budget]"
                    if shortened
                    else ""
                )
                task_truncated = True
                continue
            raise TokenBudgetError(
                f"Serialized MCP/JSON framing requires {used} tokens, exceeding the "
                f"{budget}-token hard budget even after evidence and task removal."
            )

    def _account_payload(
        self,
        base: ContextBundle,
        counter: TokenCounter,
        budget: int,
        dropped_evidence: int,
        input_usd_per_million: float | None,
        monthly_ai_credits: int | None,
        mcp_host: MCPHost | None,
    ) -> ContextBundle:
        envelope = host_envelope_profile(mcp_host) if mcp_host is not None else None
        bundle = replace(
            base,
            tokenizer=counter.tokenizer,
            target_model=counter.target_model,
            hard_budget=budget,
            mcp_host=mcp_host,
            accounting_scope=(
                envelope.scope if envelope is not None else "athena-tool-result-only"
            ),
            dropped_evidence=dropped_evidence,
            accounting_format=(
                envelope.format
                if envelope is not None
                and base.projection_id == FULL_PROJECTION
                and base.response_representation == "structured-compat-v1"
                else (
                    f"{mcp_host}:mcp-call-tool-result:"
                    f"{base.response_representation}:{base.projection_id}"
                )
                if envelope is not None
                else f"{base.projection_id}:json"
            ),
        )
        for _ in range(12):
            payload = projection_json(bundle)
            accounted = serialize_projected_result(bundle, mcp_host)
            payload_estimated = self._estimate_tokens(payload)
            estimated = self._estimate_tokens(accounted)
            provider_count = self._count_tokens(counter, accounted)
            selected = provider_count.value if provider_count.use_for_budget else None
            exact = provider_count.value if provider_count.exact else None
            used = selected if selected is not None else estimated
            input_credits = (
                round(used * input_usd_per_million / 10_000, 6)
                if input_usd_per_million is not None
                else None
            )
            monthly_payloads = (
                int(monthly_ai_credits / input_credits)
                if monthly_ai_credits is not None and input_credits
                else None
            )
            updated = replace(
                bundle,
                estimated_tokens=estimated,
                exact_tokens=exact,
                provider_tokens=selected,
                tokenizer=provider_count.tokenizer,
                token_count_source=(
                    "local-exact"
                    if provider_count.exact
                    else (
                        "provider-estimate"
                        if provider_count.use_for_budget
                        else "heuristic-estimate"
                    )
                ),
                remaining_budget=budget - used,
                serialized_bytes=len(payload.encode("utf-8")),
                accounted_bytes=len(accounted.encode("utf-8")),
                host_envelope_overhead_estimated_tokens=max(0, estimated - payload_estimated),
                estimated_input_ai_credits=input_credits,
                monthly_ai_credit_budget=monthly_ai_credits,
                estimated_monthly_athena_payloads=monthly_payloads,
                ai_credit_scope=(
                    "athena-input-only-uncached" if input_credits is not None else None
                ),
            )
            if updated == bundle:
                return bundle
            bundle = updated
        return bundle

    def _estimate_tokens(self, text: str) -> int:
        return self._token_cache.get_or_compute(
            ("estimated-utf8-v1", text), lambda: estimate_tokens(text)
        )

    def _count_tokens(self, counter: TokenCounter, text: str) -> TokenCount:
        return self._provider_token_cache.get_or_compute(
            (f"{counter.tokenizer}:{counter.target_model}", text), lambda: counter.count(text)
        )


def _compact_source_chunk(chunk: Chunk, max_lines: int) -> Chunk:
    lines = chunk.content.splitlines()
    if len(lines) <= max_lines:
        return chunk
    content = "\n".join(lines[:max_lines]) + "\n...[Athena: secondary evidence compressed]"
    return Chunk(
        chunk.chunk_id,
        chunk.path,
        chunk.start_line,
        chunk.start_line + max_lines - 1,
        content,
        chunk.content_hash,
        chunk.symbol_id,
        chunk.language,
        chunk.tags,
    )


def _truncate_chunk(chunk: Chunk, tokens: int) -> Chunk:
    char_budget = max(80, int(tokens * 3.6))
    content = chunk.content[:char_budget].rstrip() + "\n...[Athena context truncated]"
    return Chunk(
        chunk.chunk_id,
        chunk.path,
        chunk.start_line,
        chunk.end_line,
        content,
        chunk.content_hash,
        chunk.symbol_id,
        chunk.language,
        chunk.tags,
    )


def _overlap_ratio(left: Chunk, right: Chunk) -> float:
    if left.path != right.path:
        return 0.0
    overlap = max(
        0, min(left.end_line, right.end_line) - max(left.start_line, right.start_line) + 1
    )
    smaller = max(
        1, min(left.end_line - left.start_line + 1, right.end_line - right.start_line + 1)
    )
    return overlap / smaller


def _requested_tags(task: str) -> set[str]:
    lowered = task.casefold()
    tags: set[str] = set()
    if any(word in lowered for word in ("test", "junit", "pytest", "coverage")):
        tags.add("test")
    if any(
        word in lowered
        for word in ("config", "property", "properties", "environment", "yaml", "yml")
    ):
        tags.add("configuration")
    if any(
        word in lowered for word in ("database", "table", "sql", "migration", "flyway", "persist")
    ):
        tags.update({"sql", "migration", "repository", "entity"})
    if any(word in lowered for word in ("endpoint", "controller", "api", "http")):
        tags.add("controller")
    if any(word in lowered for word in ("document", "documentation", "docs", "readme", "adr")):
        tags.add("markdown")
    return tags
