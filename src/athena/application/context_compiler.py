from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any

from athena.context_projection import (
    CLARIFICATION_PROJECTION,
    ECONOMY_PROJECTION,
    mcp_text_result,
    projection_payload,
)
from athena.daemon import daemon_is_fresh
from athena.domain import ContextBundle
from athena.errors import AthenaError
from athena.mcp_envelope import MCPHost
from athena.orchestrator import AthenaRuntime
from athena.retrieval import RetrievalRequestKind


@dataclass(frozen=True, slots=True)
class _ContinuationState:
    initial_query: str
    persona_id: str
    generation: int
    returned_chunk_ids: frozenset[str]
    expires_at: float


class ContinuationStore:
    """Short-lived, process-local continuation state with opaque identifiers."""

    def __init__(self, ttl_minutes: int = 45) -> None:
        self._ttl_seconds = ttl_minutes * 60
        self._states: dict[str, _ContinuationState] = {}
        self._secret = secrets.token_bytes(32)

    def token_for(self, query: str, persona: str | None, generation: int) -> str:
        identity = f"{generation}\0{persona or 'auto'}\0{query}".encode()
        digest = hmac.new(self._secret, identity, hashlib.sha256).hexdigest()[:32]
        return f"ctx_{digest}"

    def issue(
        self,
        initial_query: str,
        persona_id: str,
        generation: int,
        returned_chunk_ids: frozenset[str],
        token: str | None = None,
        now: float | None = None,
    ) -> str:
        timestamp = time.monotonic() if now is None else now
        self._prune(timestamp)
        issued = token or ("ctx_" + secrets.token_urlsafe(18))
        self._states[issued] = _ContinuationState(
            initial_query,
            persona_id,
            generation,
            returned_chunk_ids,
            timestamp + self._ttl_seconds,
        )
        return issued

    def get(self, token: str, generation: int, now: float | None = None) -> _ContinuationState:
        timestamp = time.monotonic() if now is None else now
        self._prune(timestamp)
        state = self._states.get(token)
        if state is None:
            raise AthenaError("Continuation token is unknown or expired.")
        if state.generation != generation:
            self._states.pop(token, None)
            raise AthenaError(
                "Continuation token is stale because the repository index changed; "
                "start a new repository_context request."
            )
        return state

    def replace(
        self,
        token: str,
        state: _ContinuationState,
        returned_chunk_ids: frozenset[str],
        generation: int,
        now: float | None = None,
    ) -> None:
        timestamp = time.monotonic() if now is None else now
        self._states[token] = _ContinuationState(
            state.initial_query,
            state.persona_id,
            generation,
            state.returned_chunk_ids | returned_chunk_ids,
            timestamp + self._ttl_seconds,
        )

    def _prune(self, now: float) -> None:
        expired = [token for token, state in self._states.items() if state.expires_at <= now]
        for token in expired:
            self._states.pop(token, None)


@dataclass(frozen=True, slots=True)
class CompiledContext:
    bundle: ContextBundle
    payload: dict[str, Any]

    def mcp_result(self) -> Any:
        if self.bundle.response_representation == "compact-text-v1":
            return mcp_text_result(self.bundle)
        return self.payload


class ContextCompiler:
    """Provider-neutral context application service shared by MCP and future clients."""

    def __init__(
        self,
        runtime: AthenaRuntime,
        host: MCPHost,
        continuations: ContinuationStore | None = None,
    ) -> None:
        self.runtime = runtime
        self.host = host
        settings = runtime.config.mcp.economy
        self.settings = settings
        self.continuations = continuations or ContinuationStore(settings.continuation_ttl_minutes)

    def compile(
        self,
        query: str,
        persona: str | None = None,
        continuation_token: str | None = None,
        request_kind: RetrievalRequestKind = "context",
    ) -> CompiledContext:
        normalized_query = query.strip()
        if not normalized_query:
            raise AthenaError("query must not be empty")
        if len(normalized_query) > 12_000:
            raise AthenaError("query exceeds the 12,000-character safety limit")
        if request_kind == "clarify" and continuation_token is not None:
            raise AthenaError("Clarification requests do not accept continuation tokens.")

        generation = self.runtime.store.index_generation()
        previous: _ContinuationState | None = None
        if continuation_token:
            previous = self.continuations.get(continuation_token, generation)

        scanned = 0
        if not daemon_is_fresh(self.runtime.root, self.runtime.config):
            report = self.runtime.scan()
            scanned = report.scanned + report.deleted
        if previous is not None and scanned:
            raise AthenaError(
                "Continuation token is stale because source files changed; "
                "start a new repository_context request."
            )

        generation = self.runtime.store.index_generation()
        excluded = frozenset[str]()
        effective_query = normalized_query
        effective_persona = persona
        if previous is not None:
            if persona is not None and persona != previous.persona_id:
                raise AthenaError("A continuation must use the persona from its initial request.")
            effective_persona = previous.persona_id
            excluded = previous.returned_chunk_ids
            effective_query = f"{previous.initial_query}\nContinuation focus: {normalized_query}"

        output_token = (
            None
            if request_kind == "clarify"
            else continuation_token
            or self.continuations.token_for(normalized_query, persona, generation)
        )
        clarification = request_kind == "clarify"
        bundle = self.runtime.context(
            effective_query,
            effective_persona,
            profile=self.settings.profile,
            tokenizer_provider=self.settings.tokenizer_provider,
            target_model=self.settings.target_model,
            mcp_host=self.host,
            projection_id=(CLARIFICATION_PROJECTION if clarification else ECONOMY_PROJECTION),
            response_representation=self.settings.response_representation,
            continuation_token=output_token,
            excluded_chunk_ids=excluded,
            max_context_tokens=(
                self.settings.clarification_max_tokens
                if clarification
                else self.settings.max_context_tokens
            ),
            incremental_files_scanned=scanned,
            request_kind=request_kind,
            clarification_max_candidates=self.settings.clarification_max_candidates,
            clarification_confidence_threshold=(
                self.settings.clarification_confidence_threshold
            ),
            clarification_margin_threshold=self.settings.clarification_margin_threshold,
        )
        returned = frozenset(hit.chunk.chunk_id for hit in bundle.hits)
        if clarification:
            return CompiledContext(bundle, projection_payload(bundle))
        assert output_token is not None
        if previous is None:
            self.continuations.issue(
                normalized_query,
                bundle.persona.persona_id,
                generation,
                returned,
                token=output_token,
            )
        else:
            self.continuations.replace(output_token, previous, returned, generation)
        return CompiledContext(bundle, projection_payload(bundle))
