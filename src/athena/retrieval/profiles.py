from __future__ import annotations

import re
from dataclasses import replace

from athena.domain import Persona
from athena.errors import ConfigurationError

_PROFILES = frozenset({"economy", "copilot-economy", "eco", "balanced", "deep", "auto"})


def resolve_profile(task: str, requested: str | None) -> str:
    profile = (requested or "auto").casefold()
    if profile not in _PROFILES:
        raise ConfigurationError(
            f"Unknown retrieval profile: {profile}. "
            "Use economy, copilot-economy, eco, balanced, deep, or auto."
        )
    if profile != "auto":
        return profile
    lowered = task.casefold()
    if any(
        term in lowered
        for term in (
            "architecture",
            "workflow",
            "cross-module",
            "cross module",
            "migration",
            "system-wide",
        )
    ):
        return "deep"
    if re.search(r"\b[A-Z][A-Za-z0-9_]{2,}\b", task) and len(task.split()) <= 12:
        return "eco"
    return "balanced"


def apply_profile(persona: Persona, profile: str) -> Persona:
    policy = persona.policy
    if profile in {"economy", "copilot-economy"}:
        policy = replace(
            policy,
            max_context_tokens=min(policy.max_context_tokens, 1200),
            max_chunks_per_file=1,
            graph_depth=min(policy.graph_depth, 1),
        )
    elif profile == "eco":
        policy = replace(
            policy,
            max_context_tokens=min(policy.max_context_tokens, 1800),
            max_chunks_per_file=min(policy.max_chunks_per_file, 2),
            graph_depth=min(policy.graph_depth, 1),
        )
    elif profile == "deep":
        policy = replace(
            policy,
            max_context_tokens=max(policy.max_context_tokens, 6000),
            max_chunks_per_file=max(policy.max_chunks_per_file, 4),
            graph_depth=max(policy.graph_depth, 3),
        )
    return replace(persona, policy=policy)
