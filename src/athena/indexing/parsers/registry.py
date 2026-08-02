from __future__ import annotations

from pathlib import Path

from athena.config import SemanticConfig
from athena.indexing.models import AnalysisResult
from athena.indexing.parsers.base import SourceParser
from athena.indexing.parsers.config import ConfigurationParser
from athena.indexing.parsers.generic import GenericParser
from athena.indexing.parsers.java import JavaParser
from athena.indexing.parsers.sql import SqlParser
from athena.indexing.semantic import SemanticPluginRegistry


class _SemanticParser:
    def __init__(self, structural: SourceParser, semantic: SemanticPluginRegistry) -> None:
        self.structural = structural
        self.semantic = semantic
        self.extensions = structural.extensions

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult:
        structural = self.structural.analyze(path, text, digest)
        return self.semantic.enrich(path, text, digest, structural)


class ParserRegistry:
    def __init__(self, semantic_config: SemanticConfig | None = None) -> None:
        self._parsers: tuple[SourceParser, ...] = (
            JavaParser(),
            ConfigurationParser(),
            SqlParser(),
            GenericParser(),
        )
        self.semantic = SemanticPluginRegistry(semantic_config or SemanticConfig())

    def parser_for(self, path: Path) -> SourceParser:
        suffix = path.suffix.casefold()
        for parser in self._parsers:
            if suffix in parser.extensions:
                return _SemanticParser(parser, self.semantic)
        return _SemanticParser(GenericParser(), self.semantic)
