from __future__ import annotations

import json
from collections.abc import Sequence
from html import escape
from pathlib import Path
from typing import Any

from athena.domain import GraphNode
from athena.storage import SQLiteStore


def export_graph(store: SQLiteStore, destination: Path, format: str = "json") -> Path:
    nodes, edges = store.export_graph()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if format == "json":
        payload = {
            "nodes": [
                {
                    "id": n.node_id,
                    "kind": n.kind,
                    "name": n.name,
                    "qualified_name": n.qualified_name,
                    "path": n.path,
                    "start_line": n.start_line,
                    "end_line": n.end_line,
                    "metadata": n.metadata,
                }
                for n in nodes
            ],
            "edges": edges,
        }
        destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elif format == "graphml":
        destination.write_text(_graphml(nodes, edges), encoding="utf-8")
    elif format == "mermaid":
        destination.write_text(_mermaid(nodes, edges), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported graph export format: {format}")
    return destination


def _graphml(nodes: Sequence[GraphNode], edges: list[dict[str, Any]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '  <key id="name" for="node" attr.name="name" attr.type="string"/>',
        '  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '  <graph id="athena" edgedefault="directed">',
    ]
    for node in nodes:
        lines.append(
            f'    <node id="{escape(node.node_id)}"><data key="kind">{escape(node.kind)}</data>'
            f'<data key="name">{escape(node.qualified_name)}</data></node>'
        )
    for index, edge in enumerate(edges):
        lines.append(
            f'    <edge id="e{index}" source="{escape(str(edge["source_id"]))}" '
            f'target="{escape(str(edge["target_id"]))}"><data key="relation">'
            f"{escape(str(edge['relation']))}</data></edge>"
        )
    lines.extend(["  </graph>", "</graphml>"])
    return "\n".join(lines) + "\n"


def _mermaid(nodes: Sequence[GraphNode], edges: list[dict[str, Any]]) -> str:
    ids = {node.node_id: f"n{index}" for index, node in enumerate(nodes)}
    names = {node.node_id: node.qualified_name for node in nodes}
    lines = ["graph TD"]
    for node_id, alias in ids.items():
        label = names[node_id].replace('"', "'")[:100]
        lines.append(f'  {alias}["{label}"]')
    for edge in edges:
        source = ids.get(str(edge["source_id"]))
        target = ids.get(str(edge["target_id"]))
        if source and target:
            relation = str(edge["relation"]).replace('"', "'")
            lines.append(f"  {source} -->|{relation}| {target}")
    return "\n".join(lines) + "\n"
