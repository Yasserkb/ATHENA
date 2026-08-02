from __future__ import annotations

from importlib import metadata
from typing import cast

from athena.config import SemanticConfig
from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.models import AnalysisResult
from athena.indexing.semantic.base import SemanticPlugin
from athena.indexing.semantic.web import WebSemanticPlugin


class SemanticPluginRegistry:
    ENTRY_POINT_GROUP = "athena.semantic_plugins"

    def __init__(
        self,
        config: SemanticConfig,
        plugins: tuple[SemanticPlugin, ...] | None = None,
    ) -> None:
        self.config = config
        self.warnings: list[str] = []
        candidates: list[SemanticPlugin] = list(plugins or (WebSemanticPlugin(),))
        if config.enabled and config.load_entry_points and plugins is None:
            candidates.extend(self._entry_point_plugins())
        enabled = set(config.enabled_plugins)
        disabled = set(config.disabled_plugins)
        selected: dict[str, SemanticPlugin] = {}
        for plugin in candidates:
            plugin_id = getattr(plugin, "plugin_id", "")
            if not plugin_id:
                self.warnings.append("Ignored semantic plugin without plugin_id")
                continue
            if getattr(plugin, "api_version", "") != "1":
                self.warnings.append(
                    f"Ignored semantic plugin {plugin_id}: unsupported API "
                    f"{getattr(plugin, 'api_version', '<missing>')}"
                )
                continue
            if plugin_id in disabled or (enabled and plugin_id not in enabled):
                continue
            if plugin_id in selected:
                self.warnings.append(f"Ignored duplicate semantic plugin: {plugin_id}")
                continue
            selected[plugin_id] = plugin
        for plugin_id in sorted(enabled - selected.keys()):
            self.warnings.append(f"Enabled semantic plugin was not found: {plugin_id}")
        self.plugins = tuple(selected[key] for key in sorted(selected)) if config.enabled else ()

    def status(self) -> dict[str, object]:
        return {
            "api_version": "1",
            "enabled": self.config.enabled,
            "load_entry_points": self.config.load_entry_points,
            "plugins": [plugin.plugin_id for plugin in self.plugins],
            "warnings": list(self.warnings),
        }

    def _entry_point_plugins(self) -> list[SemanticPlugin]:
        loaded: list[SemanticPlugin] = []
        for entry_point in metadata.entry_points().select(group=self.ENTRY_POINT_GROUP):
            try:
                factory = entry_point.load()
                plugin = factory() if isinstance(factory, type) else factory
                loaded.append(cast(SemanticPlugin, plugin))
            except Exception as exc:
                self.warnings.append(
                    f"Failed to load semantic plugin {entry_point.name}: "
                    f"{type(exc).__name__}: {exc}"
                )
        return loaded

    def enrich(
        self,
        path: str,
        text: str,
        digest: str,
        structural: AnalysisResult,
    ) -> AnalysisResult:
        applicable = [
            plugin
            for plugin in self.plugins
            if "." + path.rsplit(".", 1)[-1].casefold() in plugin.extensions
        ]
        results = [structural]
        warnings = list(self.warnings)
        for plugin in applicable:
            try:
                results.append(plugin.analyze(path, text, digest, structural))
            except Exception as exc:
                warnings.append(
                    f"Semantic plugin {plugin.plugin_id} failed for {path}: "
                    f"{type(exc).__name__}: {exc}"
                )
        return _merge_results(results, tuple(warnings))


def _merge_results(
    results: list[AnalysisResult],
    registry_warnings: tuple[str, ...],
) -> AnalysisResult:
    nodes: dict[str, GraphNode] = {}
    edges: dict[tuple[str, str, str, str, int, str], Edge] = {}
    symbols: dict[str, Symbol] = {}
    warnings = list(registry_warnings)
    for result in results:
        nodes.update((node.node_id, node) for node in result.nodes)
        for edge in result.edges:
            key = (
                edge.source_id,
                edge.relation,
                edge.target_id,
                edge.evidence.path,
                edge.evidence.start_line,
                edge.evidence.extractor,
            )
            edges[key] = edge
        symbols.update((symbol.node.node_id, symbol) for symbol in result.symbols)
        warnings.extend(result.warnings)
    return AnalysisResult(
        tuple(nodes.values()),
        tuple(edges.values()),
        tuple(symbols.values()),
        warnings=tuple(dict.fromkeys(warnings)),
    )
