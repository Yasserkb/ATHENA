from __future__ import annotations

from dataclasses import dataclass

from athena.domain import Chunk, Edge, GraphNode, Symbol


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    nodes: tuple[GraphNode, ...]
    edges: tuple[Edge, ...]
    symbols: tuple[Symbol, ...]
    chunks: tuple[Chunk, ...] = ()
    warnings: tuple[str, ...] = ()
