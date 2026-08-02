from __future__ import annotations

import re
from dataclasses import dataclass

from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.common import evidence, external_node
from athena.indexing.models import AnalysisResult
from athena.indexing.semantic.contracts import http_contract, join_routes

_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;", re.MULTILINE)
_TYPE = re.compile(
    r"(?P<annotations>(?:^\s*@[^\n]+\n)*)"
    r"^\s*(?:(?:public|protected|private|abstract|final|sealed|non-sealed|static)\s+)*"
    r"(?P<kind>class|interface|record|enum)\s+(?P<name>[A-Za-z_]\w*)"
    r"(?P<tail>[^\{]*)\{",
    re.MULTILINE,
)
_METHOD = re.compile(
    r"(?P<annotations>(?:^\s*@[^\n]+\n)*)"
    r"^\s*(?:(?:public|protected|private|static|final|abstract|synchronized|native|default)\s+)+"
    r"(?:<[^>]+>\s*)?(?P<return>[\w.$<>?, @\[\]]+)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<params>[^)]*)\)"
    r"(?:\s+throws\s+[^\{;]+)?\s*(?P<term>\{|;)",
    re.MULTILINE,
)
_FIELD = re.compile(
    r"^\s*(?:(?:private|protected|public)\s+)(?:static\s+)?(?:final\s+)?"
    r"(?P<type>[A-Za-z_][\w.$<>?, ]*)\s+(?P<name>[A-Za-z_]\w*)\s*(?:=|;)",
    re.MULTILINE,
)
_ANNOTATION = re.compile(r"@([A-Za-z_]\w*)(?:\(([^)]*)\))?")
_ENDPOINT = {
    "GetMapping",
    "PostMapping",
    "PutMapping",
    "PatchMapping",
    "DeleteMapping",
    "RequestMapping",
}
_CONFIG_REF = re.compile(r"\$\{([A-Za-z0-9_.-]+)(?::[^}]*)?}")
_CALL = re.compile(r"(?:(?P<receiver>[A-Za-z_]\w*)\s*\.\s*)?(?P<name>[A-Za-z_]\w*)\s*\(")
_SKIP_CALLS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "throw",
    "new",
    "super",
    "this",
    "synchronized",
    "assert",
    "try",
}


@dataclass(frozen=True, slots=True)
class _TypeScope:
    node: GraphNode
    open_offset: int
    close_offset: int
    start_line: int
    end_line: int
    base_route: str


class JavaParser:
    extensions = frozenset({".java"})

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult:
        package_match = _PACKAGE.search(text)
        package = package_match.group(1) if package_match else ""
        imports = {
            name.rsplit(".", 1)[-1]: name
            for name in _IMPORT.findall(text)
            if not name.endswith(".*")
        }
        lines = text.splitlines()
        file_node = GraphNode(
            f"file::{path}",
            "file",
            path.rsplit("/", 1)[-1],
            path,
            path=path,
            start_line=1,
            end_line=max(1, len(lines)),
        )
        nodes: dict[str, GraphNode] = {file_node.node_id: file_node}
        edges: list[Edge] = []
        symbols: list[Symbol] = []

        package_node = GraphNode(
            f"package::{package or '<default>'}",
            "package",
            package or "<default>",
            package or "<default>",
        )
        nodes[package_node.node_id] = package_node
        edges.append(
            Edge(
                package_node.node_id,
                "CONTAINS",
                file_node.node_id,
                evidence(path, 1, 1, digest, "java-regex"),
            )
        )

        for imported in _IMPORT.findall(text):
            target = external_node("import", imported)
            nodes[target.node_id] = target
            line = _line_at(text, text.find(imported))
            edges.append(
                Edge(
                    file_node.node_id,
                    "IMPORTS",
                    target.node_id,
                    evidence(path, line, line, digest, "java-regex"),
                    0.98,
                )
            )

        scopes: list[_TypeScope] = []
        for match in _TYPE.finditer(text):
            name = match.group("name")
            kind = match.group("kind")
            qname = f"{package}.{name}" if package else name
            start_line = _line_at(text, match.start())
            close_offset = _matching_brace(text, match.end() - 1)
            end_line = _line_at(text, close_offset) if close_offset >= 0 else start_line
            annotations = _annotations(match.group("annotations"))
            metadata = {
                "package": package,
                "annotations": [a[0] for a in annotations],
                "layer": _layer(name, annotations),
            }
            node = GraphNode(
                f"java::{qname}", kind, name, qname, path, start_line, end_line, metadata
            )
            nodes[node.node_id] = node
            symbols.append(Symbol(node, body_start_line=start_line, body_end_line=end_line))
            scopes.append(
                _TypeScope(
                    node,
                    match.end() - 1,
                    close_offset if close_offset >= 0 else len(text),
                    start_line,
                    end_line,
                    _annotation_route(annotations, "RequestMapping"),
                )
            )
            edges.append(
                Edge(
                    file_node.node_id,
                    "DEFINES",
                    node.node_id,
                    evidence(path, start_line, end_line, digest, "java-regex"),
                )
            )
            edges.append(
                Edge(
                    package_node.node_id,
                    "CONTAINS",
                    node.node_id,
                    evidence(path, start_line, start_line, digest, "java-regex"),
                )
            )
            self._add_annotations(nodes, edges, node, annotations, path, start_line, digest)
            self._add_inheritance(
                nodes, edges, node, match.group("tail"), imports, package, path, start_line, digest
            )

        for scope in scopes:
            body = text[scope.open_offset + 1 : scope.close_offset]
            body_base = scope.open_offset + 1
            fields = self._fields(
                nodes, edges, scope, body, body_base, imports, package, path, text, digest
            )
            self._methods(
                nodes,
                edges,
                symbols,
                scope,
                body,
                body_base,
                fields,
                imports,
                package,
                path,
                text,
                digest,
            )
            for config_match in _CONFIG_REF.finditer(body):
                key = config_match.group(1)
                config_node = external_node("configuration_key", key)
                nodes[config_node.node_id] = config_node
                line = _line_at(text, body_base + config_match.start())
                edges.append(
                    Edge(
                        scope.node.node_id,
                        "CONFIGURED_BY",
                        config_node.node_id,
                        evidence(path, line, line, digest, "java-regex"),
                        0.99,
                    )
                )

        return AnalysisResult(tuple(nodes.values()), tuple(edges), tuple(symbols))

    @staticmethod
    def _add_annotations(
        nodes: dict[str, GraphNode],
        edges: list[Edge],
        owner: GraphNode,
        annotations: list[tuple[str, str]],
        path: str,
        line: int,
        digest: str,
    ) -> None:
        for ann, args in annotations:
            target = external_node("annotation", ann)
            nodes[target.node_id] = target
            edges.append(
                Edge(
                    owner.node_id,
                    "ANNOTATED_WITH",
                    target.node_id,
                    evidence(path, line, line, digest, "java-regex"),
                    metadata={"arguments": args},
                )
            )

    @staticmethod
    def _add_inheritance(
        nodes: dict[str, GraphNode],
        edges: list[Edge],
        owner: GraphNode,
        tail: str,
        imports: dict[str, str],
        package: str,
        path: str,
        line: int,
        digest: str,
    ) -> None:
        ext = re.search(r"\bextends\s+([\w.$]+)", tail)
        if ext:
            qname = _qualify(ext.group(1), imports, package)
            target = external_node("type", qname)
            nodes[target.node_id] = target
            edges.append(
                Edge(
                    owner.node_id,
                    "EXTENDS",
                    target.node_id,
                    evidence(path, line, line, digest, "java-regex"),
                )
            )
        impl = re.search(r"\bimplements\s+([^\{]+)", tail)
        if impl:
            for name in impl.group(1).split(","):
                qname = _qualify(name.strip().split("<", 1)[0], imports, package)
                target = external_node("type", qname)
                nodes[target.node_id] = target
                edges.append(
                    Edge(
                        owner.node_id,
                        "IMPLEMENTS",
                        target.node_id,
                        evidence(path, line, line, digest, "java-regex"),
                    )
                )

    @staticmethod
    def _fields(
        nodes: dict[str, GraphNode],
        edges: list[Edge],
        scope: _TypeScope,
        body: str,
        body_base: int,
        imports: dict[str, str],
        package: str,
        path: str,
        text: str,
        digest: str,
    ) -> dict[str, str]:
        fields: dict[str, str] = {}
        for match in _FIELD.finditer(body):
            raw_type = match.group("type").strip()
            base_type = re.sub(r"<.*>", "", raw_type).strip().split()[-1]
            qname = _qualify(base_type, imports, package)
            fields[match.group("name")] = qname
            target = external_node("type", qname)
            nodes[target.node_id] = target
            line = _line_at(text, body_base + match.start())
            edges.append(
                Edge(
                    scope.node.node_id,
                    "DEPENDS_ON",
                    target.node_id,
                    evidence(path, line, line, digest, "java-regex"),
                    0.9,
                    {"field": match.group("name")},
                )
            )
        return fields

    def _methods(
        self,
        nodes: dict[str, GraphNode],
        edges: list[Edge],
        symbols: list[Symbol],
        scope: _TypeScope,
        body: str,
        body_base: int,
        fields: dict[str, str],
        imports: dict[str, str],
        package: str,
        path: str,
        text: str,
        digest: str,
    ) -> None:
        for match in _METHOD.finditer(body):
            name = match.group("name")
            params = [x for x in _split_params(match.group("params")) if x]
            arity = len(params)
            method_id = f"{scope.node.node_id}#{name}/{arity}"
            start_offset = body_base + match.start()
            start_line = _line_at(text, start_offset)
            if match.group("term") == "{":
                open_offset = body_base + match.end() - 1
                close_offset = _matching_brace(text, open_offset)
                end_line = _line_at(text, close_offset) if close_offset >= 0 else start_line
                method_body = text[
                    open_offset + 1 : close_offset if close_offset >= 0 else len(text)
                ]
            else:
                close_offset = body_base + match.end()
                end_line = start_line
                method_body = ""
            node = GraphNode(
                method_id,
                "method",
                name,
                f"{scope.node.qualified_name}#{name}/{arity}",
                path,
                start_line,
                end_line,
                {"return_type": match.group("return").strip(), "arity": arity},
            )
            nodes[node.node_id] = node
            symbols.append(Symbol(node, match.group(0).strip(), start_line, end_line))
            edges.append(
                Edge(
                    scope.node.node_id,
                    "DEFINES",
                    node.node_id,
                    evidence(path, start_line, end_line, digest, "java-regex"),
                )
            )
            annotations = _annotations(match.group("annotations"))
            self._add_annotations(nodes, edges, node, annotations, path, start_line, digest)
            for annotation, args in annotations:
                if annotation in _ENDPOINT:
                    route = join_routes(scope.base_route, _first_string(args) or "/")
                    method = _http_method(annotation, args)
                    contract = http_contract(method, route)
                    endpoint = GraphNode(
                        f"endpoint::{scope.node.qualified_name}::{name}/{arity}::{contract}",
                        "endpoint",
                        contract,
                        contract,
                        path,
                        start_line,
                        start_line,
                        {
                            "framework": "spring",
                            "http_annotation": annotation,
                            "http_method": method,
                            "route": route,
                            "contract_type": "http",
                        },
                    )
                    nodes[endpoint.node_id] = endpoint
                    ev = evidence(path, start_line, start_line, digest, "java-regex")
                    edges.append(Edge(scope.node.node_id, "EXPOSES_ENDPOINT", endpoint.node_id, ev))
                    edges.append(Edge(endpoint.node_id, "HANDLED_BY", node.node_id, ev))
            seen_calls: set[str] = set()
            for call in _CALL.finditer(method_body):
                call_name = call.group("name")
                if call_name in _SKIP_CALLS or (call_name == name and not call.group("receiver")):
                    continue
                receiver = call.group("receiver")
                if receiver and receiver in fields:
                    target_name = f"{fields[receiver]}#{call_name}"
                elif receiver:
                    target_name = f"{receiver}.{call_name}"
                else:
                    target_name = call_name
                if target_name in seen_calls:
                    continue
                seen_calls.add(target_name)
                target = external_node("method", target_name)
                nodes[target.node_id] = target
                call_line = (
                    _line_at(text, (close_offset - len(method_body)) + call.start())
                    if method_body
                    else start_line
                )
                edges.append(
                    Edge(
                        node.node_id,
                        "CALLS",
                        target.node_id,
                        evidence(path, call_line, call_line, digest, "java-regex"),
                        0.72,
                    )
                )
                if len(seen_calls) >= 40:
                    break


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _matching_brace(text: str, open_offset: int) -> int:
    if open_offset < 0 or open_offset >= len(text) or text[open_offset] != "{":
        return -1
    depth = 0
    in_string: str | None = None
    escaped = False
    in_line_comment = False
    in_block_comment = False
    i = open_offset
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if char == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            i += 1
            continue
        if char == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if char == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if char in {'"', "'"}:
            in_string = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _annotations(raw: str) -> list[tuple[str, str]]:
    return [(m.group(1), (m.group(2) or "").strip()) for m in _ANNOTATION.finditer(raw or "")]


def _first_string(raw: str) -> str | None:
    match = re.search(r'["\']([^"\']+)["\']', raw or "")
    return match.group(1) if match else None


def _annotation_route(annotations: list[tuple[str, str]], name: str) -> str:
    for annotation, args in annotations:
        if annotation == name:
            return _first_string(args) or ""
    return ""


def _http_method(annotation: str, args: str) -> str:
    methods = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "PatchMapping": "PATCH",
        "DeleteMapping": "DELETE",
    }
    if annotation in methods:
        return methods[annotation]
    request_method = re.search(r"RequestMethod\.([A-Z]+)", args)
    return request_method.group(1) if request_method else "ANY"


def _qualify(name: str, imports: dict[str, str], package: str) -> str:
    clean = name.strip().replace("[]", "")
    if "." in clean:
        return clean
    if clean in imports:
        return imports[clean]
    if clean in {"String", "Long", "Integer", "Boolean", "Double", "Float", "Object", "Void"}:
        return f"java.lang.{clean}"
    return f"{package}.{clean}" if package else clean


def _split_params(raw: str) -> list[str]:
    if not raw.strip():
        return []
    values: list[str] = []
    depth = 0
    current: list[str] = []
    for char in raw:
        if char in "<([":
            depth += 1
        elif char in ">)]":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        values.append("".join(current).strip())
    return values


def _layer(name: str, annotations: list[tuple[str, str]]) -> str:
    annotation_names = {x[0] for x in annotations}
    if annotation_names & {"RestController", "Controller"} or name.endswith("Controller"):
        return "controller"
    if "Repository" in annotation_names or name.endswith("Repository"):
        return "repository"
    if (
        annotation_names & {"Service", "Component"}
        or name.endswith("Service")
        or name.endswith("ServiceImpl")
    ):
        return "service"
    if annotation_names & {"Entity", "MappedSuperclass"}:
        return "entity"
    if "Configuration" in annotation_names or name.endswith("Configuration"):
        return "configuration"
    if name.endswith(("Test", "IT", "IntegrationTest")):
        return "test"
    return "domain"
