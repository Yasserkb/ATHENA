from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from athena.domain import Edge, Evidence, GraphNode
from athena.indexing.common import content_hash
from athena.storage import SQLiteStore

DERIVER_VERSION = "3"
_RELATIONS = {
    "DEPENDS_ON",
    "EXTENDS",
    "IMPLEMENTS",
    "CALLS",
    "CALLS_ENDPOINT",
    "CONFIGURED_BY",
}


class ArchitectureDeriver:
    """Derive relations only for file owners affected by an index update."""

    def derive(
        self,
        store: SQLiteStore,
        repository_id: str,
        repository_name: str,
        affected_paths: set[str] | None = None,
    ) -> tuple[int, int]:
        full = affected_paths is None
        owners = set(store.indexed_paths()) if affected_paths is None else set(affected_paths)
        if not owners and not full:
            return 0, 0

        repo = GraphNode(repository_id, "repository", repository_name, repository_name, "@derived")
        owner_nodes = store.nodes_for_paths(tuple(sorted(owners)))
        by_id = {node.node_id: node for node in owner_nodes}
        raw_edges = store.edges_for_evidence_paths(tuple(sorted(owners)))
        derived_nodes: dict[str, GraphNode] = {}
        derived_edges: list[Edge] = []
        resolved_dependencies: dict[str, list[GraphNode]] = defaultdict(list)

        for node in owner_nodes:
            if node.kind == "file" and node.path:
                derived_edges.append(
                    Edge(
                        repo.node_id,
                        "CONTAINS",
                        node.node_id,
                        _derived_evidence("repository containment", node.path),
                        1.0,
                    )
                )

        for raw in raw_edges:
            relation = str(raw["relation"])
            if relation not in _RELATIONS:
                continue
            source = by_id.get(str(raw["source_id"])) or store.node_by_id(str(raw["source_id"]))
            external = store.node_by_id(str(raw["target_id"]))
            if source is None or external is None or external.kind != "external_symbol":
                continue
            resolved = store.resolve_repository_node(external.qualified_name, relation)
            if resolved is None or resolved.node_id == source.node_id or not source.path:
                continue
            confidence = (
                0.96
                if relation == "CALLS_ENDPOINT"
                else 0.92
                if "." in external.qualified_name
                else 0.78
            )
            metadata = {
                "inferred_from": relation,
                "external_target": external.qualified_name,
                "source_evidence": raw["evidence_path"],
                "owner_path": source.path,
                "deriver_version": DERIVER_VERSION,
            }
            derived_edges.append(
                Edge(
                    source.node_id,
                    f"RESOLVED_{relation}",
                    resolved.node_id,
                    _derived_evidence(str(metadata), source.path),
                    confidence,
                    metadata,
                )
            )
            if relation == "DEPENDS_ON":
                resolved_dependencies[source.node_id].append(resolved)

        for node in owner_nodes:
            if not node.path or (node.metadata.get("layer") != "test" and node.kind != "test"):
                continue
            target_name = _production_name(node.name)
            target = store.resolve_repository_node(target_name, "")
            if target is not None and target.metadata.get("layer") != "test":
                derived_edges.append(
                    Edge(
                        node.node_id,
                        "TESTS",
                        target.node_id,
                        _derived_evidence(f"{node.name}->{target.name}", node.path),
                        0.9,
                        {"owner_path": node.path, "deriver_version": DERIVER_VERSION},
                    )
                )

        controllers = [
            node for node in owner_nodes if node.metadata.get("layer") == "controller" and node.path
        ]
        for controller in controllers:
            services = [
                node
                for node in resolved_dependencies.get(controller.node_id, [])
                if node.metadata.get("layer") == "service"
            ]
            for service in services:
                repositories = self._resolved_dependencies(store, service)
                repositories = [
                    node for node in repositories if node.metadata.get("layer") == "repository"
                ]
                if repositories:
                    self._add_layered_pattern(
                        controller,
                        services,
                        repositories,
                        derived_nodes,
                        derived_edges,
                    )
                    break

        if full:
            store.replace_derived_graph((repo, *derived_nodes.values()), tuple(derived_edges))
        else:
            store.upsert_global_nodes((repo,))
            store.replace_derived_graph_for_paths(
                tuple(sorted(owners)), tuple(derived_nodes.values()), tuple(derived_edges)
            )
        return len(derived_nodes) + (1 if full else 0), len(derived_edges)

    @staticmethod
    def _resolved_dependencies(store: SQLiteStore, source: GraphNode) -> list[GraphNode]:
        if not source.path:
            return []
        results: list[GraphNode] = []
        for raw in store.edges_for_evidence_paths((source.path,)):
            if raw["source_id"] != source.node_id or raw["relation"] != "DEPENDS_ON":
                continue
            external = store.node_by_id(str(raw["target_id"]))
            if external is None:
                continue
            resolved = store.resolve_repository_node(external.qualified_name, "DEPENDS_ON")
            if resolved is not None:
                results.append(resolved)
        return results

    @staticmethod
    def _add_layered_pattern(
        controller: GraphNode,
        services: Sequence[GraphNode],
        repositories: Sequence[GraphNode],
        nodes: dict[str, GraphNode],
        edges: list[Edge],
    ) -> None:
        assert controller.path is not None
        owner = controller.path
        pattern_id = f"pattern::layered::{controller.node_id}"
        pattern = GraphNode(
            pattern_id,
            "pattern",
            "Controller-Service-Repository",
            f"Controller-Service-Repository::{controller.qualified_name}",
            _owner_key(owner),
            metadata={
                "confidence": 0.88,
                "owner_path": owner,
                "deriver_version": DERIVER_VERSION,
            },
        )
        nodes[pattern.node_id] = pattern
        evidence = _derived_evidence(controller.qualified_name, owner)
        edges.append(Edge(controller.node_id, "FOLLOWS_PATTERN", pattern.node_id, evidence, 0.88))
        for member in [controller, *services, *repositories]:
            edges.append(Edge(pattern.node_id, "HAS_MEMBER", member.node_id, evidence, 0.88))


def _production_name(name: str) -> str:
    for suffix in ("IntegrationTest", "IT", "Tests", "Test"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _owner_key(owner_path: str) -> str:
    return f"@derived:{owner_path}"


def _derived_evidence(value: str, owner_path: str) -> Evidence:
    return Evidence(
        _owner_key(owner_path),
        1,
        1,
        content_hash(value),
        "architecture-deriver",
        0.85,
    )
