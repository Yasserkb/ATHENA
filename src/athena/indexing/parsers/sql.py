from __future__ import annotations

import re

from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.common import evidence
from athena.indexing.models import AnalysisResult

_TABLE = re.compile(
    r'\b(?:CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?|ALTER\s+TABLE|INSERT\s+INTO|REFERENCES)\s+([A-Za-z_][\w.$"]*)',
    re.IGNORECASE,
)


class SqlParser:
    extensions = frozenset({".sql"})

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult:
        lines = text.splitlines()
        file_node = GraphNode(
            f"file::{path}", "migration", path.rsplit("/", 1)[-1], path, path, 1, max(1, len(lines))
        )
        nodes: dict[str, GraphNode] = {file_node.node_id: file_node}
        edges: list[Edge] = []
        symbols: list[Symbol] = [
            Symbol(file_node, body_start_line=1, body_end_line=max(1, len(lines)))
        ]
        for match in _TABLE.finditer(text):
            table_name = match.group(1).replace('"', "")
            line = text.count("\n", 0, match.start()) + 1
            table = GraphNode(
                f"table::{table_name.casefold()}",
                "database_table",
                table_name.rsplit(".", 1)[-1],
                table_name,
            )
            nodes[table.node_id] = table
            edges.append(
                Edge(
                    file_node.node_id,
                    "TOUCHES_TABLE",
                    table.node_id,
                    evidence(path, line, line, digest, "sql-parser"),
                )
            )
        return AnalysisResult(tuple(nodes.values()), tuple(edges), tuple(symbols))
