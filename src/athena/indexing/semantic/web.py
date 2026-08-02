from __future__ import annotations

import re
from dataclasses import dataclass

from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.common import evidence, external_node, stable_id
from athena.indexing.models import AnalysisResult
from athena.indexing.semantic.contracts import http_contract, join_routes

_HTTP_METHODS = "get|post|put|patch|delete|options|head"
_PY_DECORATOR = re.compile(
    rf"@[\w.]+\.(?P<method>{_HTTP_METHODS})\(\s*[\"'](?P<route>[^\"']+)",
    re.I,
)
_PY_ROUTE = re.compile(
    r"@[\w.]+\.route\(\s*[\"'](?P<route>[^\"']+)[\"'](?P<args>[^)]*)\)",
    re.I,
)
_DJANGO_PATH = re.compile(
    r"\b(?:path|re_path)\(\s*[\"'](?P<route>[^\"']+)[\"']\s*,\s*(?P<handler>[\w.]+)",
    re.I,
)
_EXPRESS_ROUTE = re.compile(
    rf"\b(?:app|router)\.(?P<method>{_HTTP_METHODS})"
    r"\(\s*[\"'](?P<route>[^\"']+)[\"']\s*,\s*(?P<handler>[A-Za-z_$]\w*)",
    re.I,
)
_NEST_DECORATOR = re.compile(
    rf"@(?P<method>{_HTTP_METHODS})\(\s*(?:[\"'](?P<route>[^\"']*)[\"'])?\s*\)",
    re.I,
)
_NEST_CONTROLLER = re.compile(
    r"@Controller\(\s*(?:[\"'](?P<route>[^\"']*)[\"'])?\s*\)",
    re.I,
)
_DOTNET_ATTRIBUTE = re.compile(
    rf"\[Http(?P<method>{_HTTP_METHODS})(?:\(\s*[\"'](?P<route>[^\"']*)[\"']\s*\))?\]",
    re.I,
)
_DOTNET_ROUTE = re.compile(r"\[Route\(\s*[\"'](?P<route>[^\"']+)[\"']\s*\)]", re.I)
_DOTNET_MINIMAL = re.compile(
    rf"\bapp\.Map(?P<method>{_HTTP_METHODS})\(\s*[\"'](?P<route>[^\"']+)[\"']",
    re.I,
)
_GO_ROUTE = re.compile(
    rf"\b(?:router|r|group)\.(?P<method>{_HTTP_METHODS})"
    r"\(\s*[\"'](?P<route>[^\"']+)[\"']\s*,\s*(?P<handler>[A-Za-z_]\w*)",
    re.I,
)
_RUST_ATTRIBUTE = re.compile(
    rf"#\[(?P<method>{_HTTP_METHODS})\(\s*[\"'](?P<route>[^\"']+)[\"']\s*\)\]",
    re.I,
)
_RUST_ROUTE = re.compile(
    rf"\.route\(\s*[\"'](?P<route>[^\"']+)[\"']\s*,\s*web::(?P<method>{_HTTP_METHODS})\(\)",
    re.I,
)

_CLIENT_PATTERNS: dict[str, tuple[tuple[re.Pattern[str], str | None], ...]] = {
    ".py": (
        (
            re.compile(
                rf"\b(?:requests|httpx|client|session)\.(?P<method>{_HTTP_METHODS})"
                r"\(\s*[\"'](?P<route>https?://[^\"']+|/[^\"']*)[\"']",
                re.I,
            ),
            None,
        ),
    ),
    ".ts": (),
    ".tsx": (),
    ".js": (),
    ".jsx": (),
    ".mjs": (),
    ".cjs": (),
    ".java": (
        (
            re.compile(
                r"\.(?P<operation>getForObject|getForEntity|postForObject|postForEntity)"
                r"\(\s*[\"'](?P<route>https?://[^\"']+|/[^\"']*)[\"']"
            ),
            None,
        ),
    ),
    ".cs": (
        (
            re.compile(
                r"\.(?P<operation>GetAsync|PostAsync|PutAsync|PatchAsync|DeleteAsync)"
                r"\(\s*[\"'](?P<route>https?://[^\"']+|/[^\"']*)[\"']"
            ),
            None,
        ),
    ),
    ".go": (
        (
            re.compile(r"\bhttp\.(?P<method>Get|Post)\(\s*[\"'](?P<route>[^\"']+)[\"']"),
            None,
        ),
        (
            re.compile(
                r"\bhttp\.NewRequest\(\s*[\"'](?P<method>[A-Z]+)[\"']\s*,\s*"
                r"[\"'](?P<route>[^\"']+)[\"']"
            ),
            None,
        ),
    ),
    ".rs": (
        (
            re.compile(
                rf"\b(?:client|reqwest)::?\w*\.(?P<method>{_HTTP_METHODS})"
                r"\(\s*[\"'](?P<route>[^\"']+)[\"']",
                re.I,
            ),
            None,
        ),
    ),
}
_JS_CLIENT = re.compile(
    rf"\b(?:axios|client|http)\.(?P<method>{_HTTP_METHODS})"
    r"\(\s*[\"'`](?P<route>https?://[^\"'`]+|/[^\"'`]*)[\"'`]",
    re.I,
)
_FETCH_CLIENT = re.compile(
    r"\bfetch\(\s*[\"'`](?P<route>https?://[^\"'`]+|/[^\"'`]*)[\"'`]"
    r"(?P<options>\s*,\s*\{[^}]*\})?",
    re.I,
)


@dataclass(frozen=True, slots=True)
class _EndpointFact:
    method: str
    route: str
    line: int
    framework: str
    handler: str | None = None


@dataclass(frozen=True, slots=True)
class _ClientFact:
    method: str
    route: str
    line: int


class WebSemanticPlugin:
    api_version = "1"
    plugin_id = "builtin.web-contracts.v1"
    extensions = frozenset(
        {
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".mjs",
            ".cjs",
            ".java",
            ".cs",
            ".go",
            ".rs",
        }
    )

    def analyze(
        self,
        path: str,
        text: str,
        digest: str,
        structural: AnalysisResult,
    ) -> AnalysisResult:
        suffix = "." + path.rsplit(".", 1)[-1].casefold()
        endpoints = self._endpoints(suffix, text)
        clients = self._clients(suffix, text)
        nodes: dict[str, GraphNode] = {}
        edges: list[Edge] = []
        for endpoint_fact in endpoints:
            contract = http_contract(endpoint_fact.method, endpoint_fact.route)
            owner = _owner_for(
                structural.symbols,
                endpoint_fact.line,
                path,
                endpoint_fact.handler,
            )
            endpoint = GraphNode(
                stable_id("semantic-endpoint", path, contract, endpoint_fact.line),
                "endpoint",
                contract,
                contract,
                path,
                endpoint_fact.line,
                endpoint_fact.line,
                {
                    "framework": endpoint_fact.framework,
                    "http_method": endpoint_fact.method.upper(),
                    "route": endpoint_fact.route,
                    "contract_type": "http",
                    "semantic_plugin": self.plugin_id,
                },
            )
            nodes[endpoint.node_id] = endpoint
            ev = evidence(
                path,
                endpoint_fact.line,
                endpoint_fact.line,
                digest,
                self.plugin_id,
                0.96,
            )
            edges.append(Edge(owner.node_id, "EXPOSES_ENDPOINT", endpoint.node_id, ev, 0.96))
            edges.append(Edge(endpoint.node_id, "HANDLED_BY", owner.node_id, ev, 0.92))

        for client_fact in clients:
            contract = http_contract(client_fact.method, client_fact.route)
            owner = _owner_for(structural.symbols, client_fact.line, path)
            target = external_node("http_endpoint", contract)
            nodes[target.node_id] = target
            edges.append(
                Edge(
                    owner.node_id,
                    "CALLS_ENDPOINT",
                    target.node_id,
                    evidence(
                        path,
                        client_fact.line,
                        client_fact.line,
                        digest,
                        self.plugin_id,
                        0.9,
                    ),
                    0.9,
                    {
                        "http_method": client_fact.method.upper(),
                        "route": client_fact.route,
                    },
                )
            )
        return AnalysisResult(tuple(nodes.values()), tuple(edges), ())

    def _endpoints(self, suffix: str, text: str) -> list[_EndpointFact]:
        facts: list[_EndpointFact] = []
        if suffix == ".py":
            facts.extend(_facts(_PY_DECORATOR, text, "fastapi"))
            for match in _PY_ROUTE.finditer(text):
                methods = re.findall(r"[\"']([A-Z]+)[\"']", match.group("args"))
                for method in methods or ["GET"]:
                    facts.append(
                        _EndpointFact(
                            method,
                            match.group("route"),
                            _line_at(text, match.start()),
                            "flask",
                        )
                    )
            for match in _DJANGO_PATH.finditer(text):
                facts.append(
                    _EndpointFact(
                        "ANY",
                        match.group("route"),
                        _line_at(text, match.start()),
                        "django",
                        match.group("handler").rsplit(".", 1)[-1],
                    )
                )
        elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            for match in _EXPRESS_ROUTE.finditer(text):
                facts.append(
                    _EndpointFact(
                        match.group("method"),
                        match.group("route"),
                        _line_at(text, match.start()),
                        "express",
                        match.group("handler"),
                    )
                )
            controller = _NEST_CONTROLLER.search(text)
            prefix = controller.group("route") if controller and controller.group("route") else ""
            for fact in _facts(_NEST_DECORATOR, text, "nestjs"):
                facts.append(
                    _EndpointFact(
                        fact.method,
                        join_routes(prefix, fact.route),
                        fact.line,
                        fact.framework,
                    )
                )
        elif suffix == ".cs":
            route_match = _DOTNET_ROUTE.search(text)
            prefix = route_match.group("route") if route_match else ""
            class_match = re.search(r"\bclass\s+([A-Za-z_]\w*)", text)
            if class_match:
                prefix = prefix.replace(
                    "[controller]",
                    re.sub(r"Controller$", "", class_match.group(1), flags=re.I),
                )
            for fact in _facts(_DOTNET_ATTRIBUTE, text, "aspnet-core"):
                facts.append(
                    _EndpointFact(
                        fact.method,
                        join_routes(prefix, fact.route),
                        fact.line,
                        fact.framework,
                    )
                )
            facts.extend(_facts(_DOTNET_MINIMAL, text, "aspnet-core"))
        elif suffix == ".go":
            facts.extend(_facts(_GO_ROUTE, text, "go-http"))
        elif suffix == ".rs":
            facts.extend(_facts(_RUST_ATTRIBUTE, text, "rust-http"))
            facts.extend(_facts(_RUST_ROUTE, text, "rust-http"))
        return facts

    def _clients(self, suffix: str, text: str) -> list[_ClientFact]:
        facts: list[_ClientFact] = []
        patterns = _CLIENT_PATTERNS.get(suffix, ())
        for regex, fixed_method in patterns:
            for match in regex.finditer(text):
                method = fixed_method or _client_method(match)
                facts.append(
                    _ClientFact(
                        method,
                        match.group("route"),
                        _line_at(text, match.start()),
                    )
                )
        if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            for match in _JS_CLIENT.finditer(text):
                facts.append(
                    _ClientFact(
                        match.group("method"),
                        match.group("route"),
                        _line_at(text, match.start()),
                    )
                )
            for match in _FETCH_CLIENT.finditer(text):
                options = match.group("options") or ""
                method_match = re.search(r"\bmethod\s*:\s*[\"']([A-Z]+)[\"']", options, re.I)
                facts.append(
                    _ClientFact(
                        method_match.group(1) if method_match else "GET",
                        match.group("route"),
                        _line_at(text, match.start()),
                    )
                )
        return facts


def _facts(regex: re.Pattern[str], text: str, framework: str) -> list[_EndpointFact]:
    return [
        _EndpointFact(
            match.group("method"),
            match.groupdict().get("route") or "/",
            _line_at(text, match.start()),
            framework,
            match.groupdict().get("handler"),
        )
        for match in regex.finditer(text)
    ]


def _client_method(match: re.Match[str]) -> str:
    values = match.groupdict()
    if values.get("method"):
        return values["method"]
    operation = values.get("operation", "")
    for method in ("get", "post", "put", "patch", "delete"):
        if operation.casefold().startswith(method):
            return method
    return "GET"


def _owner_for(
    symbols: tuple[Symbol, ...],
    line: int,
    path: str,
    name: str | None = None,
) -> GraphNode:
    if name:
        named = [symbol.node for symbol in symbols if symbol.node.name == name]
        if named:
            return min(named, key=lambda node: abs(node.start_line - line))
    following = [
        symbol.node
        for symbol in symbols
        if symbol.node.kind == "method" and line <= symbol.node.start_line <= line + 8
    ]
    if following:
        return min(following, key=lambda node: node.start_line)
    containing = [
        symbol for symbol in symbols if symbol.body_start_line <= line <= symbol.body_end_line
    ]
    if containing:
        return min(
            containing,
            key=lambda symbol: symbol.body_end_line - symbol.body_start_line,
        ).node
    file_nodes = [symbol.node for symbol in symbols if symbol.node.kind == "file"]
    if file_nodes:
        return file_nodes[0]
    if symbols:
        return symbols[0].node
    return GraphNode(f"file::{path}", "file", path.rsplit("/", 1)[-1], path, path)


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
