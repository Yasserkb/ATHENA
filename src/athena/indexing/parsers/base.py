from __future__ import annotations

from typing import Protocol

from athena.indexing.models import AnalysisResult


class SourceParser(Protocol):
    extensions: frozenset[str]

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult: ...
