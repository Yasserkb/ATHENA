from __future__ import annotations

from typing import Protocol

from athena.indexing.models import AnalysisResult


class SemanticPlugin(Protocol):
    api_version: str
    plugin_id: str
    extensions: frozenset[str]

    def analyze(
        self,
        path: str,
        text: str,
        digest: str,
        structural: AnalysisResult,
    ) -> AnalysisResult: ...
