from __future__ import annotations

import re

from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.common import evidence
from athena.indexing.models import AnalysisResult

_ENV = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::[^}]*)?}")


class ConfigurationParser:
    extensions = frozenset({".yaml", ".yml", ".properties"})

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult:
        lines = text.splitlines()
        file_node = GraphNode(
            f"file::{path}", "file", path.rsplit("/", 1)[-1], path, path, 1, max(1, len(lines))
        )
        nodes: dict[str, GraphNode] = {file_node.node_id: file_node}
        edges: list[Edge] = []
        symbols: list[Symbol] = []
        keys = self._properties(lines) if path.endswith(".properties") else self._yaml(lines)
        for key, value, line in keys:
            node = GraphNode(
                f"config::{key}",
                "configuration_key",
                key.rsplit(".", 1)[-1],
                key,
                path,
                line,
                line,
                {"value_preview": value[:120]},
            )
            nodes[node.node_id] = node
            symbols.append(Symbol(node, f"{key}={value}", line, line))
            ev = evidence(path, line, line, digest, "config-parser")
            edges.append(Edge(file_node.node_id, "DEFINES", node.node_id, ev))
            for env_name in _ENV.findall(value):
                env = GraphNode(f"env::{env_name}", "environment_variable", env_name, env_name)
                nodes[env.node_id] = env
                edges.append(Edge(node.node_id, "BINDS_ENV", env.node_id, ev))
        return AnalysisResult(tuple(nodes.values()), tuple(edges), tuple(symbols))

    @staticmethod
    def _properties(lines: list[str]) -> list[tuple[str, str, int]]:
        out = []
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "!")) or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            out.append((key.strip(), value.strip(), number))
        return out

    @staticmethod
    def _yaml(lines: list[str]) -> list[tuple[str, str, int]]:
        out: list[tuple[str, str, int]] = []
        stack: list[tuple[int, str]] = []
        for number, line in enumerate(lines, 1):
            if not line.strip() or line.lstrip().startswith(("#", "- ")):
                continue
            match = re.match(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+)\s*:\s*(?P<value>.*)$", line)
            if not match:
                continue
            indent = len(match.group("indent").replace("\t", "    "))
            key = match.group("key")
            value = match.group("value").strip()
            while stack and stack[-1][0] >= indent:
                stack.pop()
            full_key = ".".join([*(x[1] for x in stack), key])
            out.append((full_key, value, number))
            if not value:
                stack.append((indent, key))
        return out
