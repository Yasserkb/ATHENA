from __future__ import annotations

import json

from athena.domain import Edge, Evidence, GraphNode, Persona
from athena.indexing.common import content_hash
from athena.storage import SQLiteStore


def write_persona_graph(store: SQLiteStore, personas: dict[str, Persona]) -> tuple[int, int]:
    fingerprint = content_hash(
        json.dumps(
            {
                persona_id: {
                    "purpose": persona.purpose,
                    "triggers": persona.triggers,
                    "rules": persona.rules,
                    "output": persona.output,
                    "policy": {
                        "start_kinds": persona.policy.start_kinds,
                        "traverse_relations": persona.policy.traverse_relations,
                        "include_tags": persona.policy.include_tags,
                        "max_context_tokens": persona.policy.max_context_tokens,
                        "max_chunks_per_file": persona.policy.max_chunks_per_file,
                        "graph_depth": persona.policy.graph_depth,
                    },
                }
                for persona_id, persona in sorted(personas.items())
            },
            sort_keys=True,
        )
    )
    if store.metadata().get("persona_graph_hash") == fingerprint:
        return 0, 0
    nodes: dict[str, GraphNode] = {}
    edges: list[Edge] = []
    for persona in personas.values():
        persona_node = GraphNode(
            f"persona::{persona.persona_id}",
            "persona",
            persona.persona_id,
            persona.persona_id,
            "@persona",
            metadata={
                "purpose": persona.purpose,
                "rules": list(persona.rules),
                "output": persona.output,
                "max_context_tokens": persona.policy.max_context_tokens,
                "graph_depth": persona.policy.graph_depth,
            },
        )
        nodes[persona_node.node_id] = persona_node
        for relation in persona.policy.traverse_relations:
            policy = GraphNode(
                f"persona-policy::relation::{relation}",
                "relation_policy",
                relation,
                relation,
                "@persona",
            )
            nodes[policy.node_id] = policy
            edges.append(
                Edge(
                    persona_node.node_id,
                    "PERSONA_TRAVERSES",
                    policy.node_id,
                    _evidence(persona.persona_id, relation),
                )
            )
        for kind in persona.policy.start_kinds:
            policy = GraphNode(
                f"persona-policy::kind::{kind}", "node_kind_policy", kind, kind, "@persona"
            )
            nodes[policy.node_id] = policy
            edges.append(
                Edge(
                    persona_node.node_id,
                    "PERSONA_STARTS_FROM",
                    policy.node_id,
                    _evidence(persona.persona_id, kind),
                )
            )
        for tag in persona.policy.include_tags:
            policy = GraphNode(f"persona-policy::tag::{tag}", "tag_policy", tag, tag, "@persona")
            nodes[policy.node_id] = policy
            edges.append(
                Edge(
                    persona_node.node_id,
                    "PERSONA_PRIORITIZES",
                    policy.node_id,
                    _evidence(persona.persona_id, tag),
                )
            )
    store.replace_persona_graph(tuple(nodes.values()), tuple(edges))
    store.set_metadata("persona_graph_hash", fingerprint)
    return len(nodes), len(edges)


def _evidence(persona: str, value: str) -> Evidence:
    return Evidence("@persona", 1, 1, content_hash(f"{persona}:{value}"), "persona-registry", 1.0)
