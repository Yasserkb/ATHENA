from __future__ import annotations

import re
from dataclasses import dataclass

from athena.domain import Edge, GraphNode, Symbol
from athena.indexing.common import evidence, external_node
from athena.indexing.models import AnalysisResult


@dataclass(frozen=True, slots=True)
class _LanguageRules:
    imports: tuple[re.Pattern[str], ...]
    definitions: tuple[tuple[re.Pattern[str], str], ...]
    namespace: re.Pattern[str] | None = None


def _patterns(*values: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(value, re.MULTILINE) for value in values)


_PYTHON = _LanguageRules(
    _patterns(r"^\s*from\s+([\w.]+)\s+import\s+", r"^\s*import\s+([\w.]+)"),
    (
        (re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.MULTILINE), "class"),
        (re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.MULTILINE), "method"),
    ),
)
_JVM = _LanguageRules(
    _patterns(r"^\s*import\s+([\w.]+)"),
    (
        (re.compile(r"^\s*(?:data\s+|sealed\s+)?class\s+([A-Za-z_]\w*)", re.MULTILINE), "class"),
        (re.compile(r"^\s*interface\s+([A-Za-z_]\w*)", re.MULTILINE), "interface"),
        (re.compile(r"^\s*(?:suspend\s+)?fun\s+([A-Za-z_]\w*)", re.MULTILINE), "method"),
    ),
    re.compile(r"^\s*package\s+([\w.]+)", re.MULTILINE),
)
_JS = _LanguageRules(
    _patterns(
        r"^\s*import(?:[\s\S]*?\s+from\s+|\s*)['\"]([^'\"]+)['\"]",
        r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    ),
    (
        (
            re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$]\w*)", re.MULTILINE),
            "class",
        ),
        (re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_$]\w*)", re.MULTILINE), "interface"),
        (
            re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$]\w*)", re.MULTILINE),
            "method",
        ),
        (
            re.compile(
                r"^\s*(?:export\s+)?const\s+([A-Za-z_$]\w*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
                re.MULTILINE,
            ),
            "method",
        ),
    ),
)
_CSHARP = _LanguageRules(
    _patterns(r"^\s*using\s+([\w.]+)\s*;"),
    (
        (
            re.compile(
                r"^\s*(?:public|internal|private|protected|abstract|sealed|partial|static|\s)*(?:class|record|struct|enum)\s+([A-Za-z_]\w*)",
                re.MULTILINE,
            ),
            "class",
        ),
        (
            re.compile(
                r"^\s*(?:public|internal|private|protected|\s)*interface\s+([A-Za-z_]\w*)",
                re.MULTILINE,
            ),
            "interface",
        ),
        (
            re.compile(
                r"^\s*(?:public|internal|private|protected|static|async|virtual|override|\s)+[\w<>?,\[\].]+\s+([A-Za-z_]\w*)\s*\(",
                re.MULTILINE,
            ),
            "method",
        ),
    ),
    re.compile(r"^\s*namespace\s+([\w.]+)", re.MULTILINE),
)
_GO = _LanguageRules(
    _patterns(r"^\s*import\s+['\"]([^'\"]+)['\"]", r"['\"]([^'\"]+)['\"]"),
    (
        (re.compile(r"^\s*type\s+([A-Za-z_]\w*)\s+(?:struct|interface)", re.MULTILINE), "class"),
        (re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", re.MULTILINE), "method"),
    ),
    re.compile(r"^\s*package\s+([\w]+)", re.MULTILINE),
)
_RUST = _LanguageRules(
    _patterns(r"^\s*use\s+([^;]+);", r"^\s*mod\s+([A-Za-z_]\w*)\s*;"),
    (
        (
            re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)", re.MULTILINE),
            "class",
        ),
        (
            re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
            "method",
        ),
    ),
)
_PHP = _LanguageRules(
    _patterns(
        r"^\s*use\s+([\\\w]+)\s*;", r"(?:require|include)(?:_once)?\s*\(?\s*['\"]([^'\"]+)['\"]"
    ),
    (
        (
            re.compile(
                r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait|enum)\s+([A-Za-z_]\w*)",
                re.MULTILINE,
            ),
            "class",
        ),
        (
            re.compile(
                r"^\s*(?:public|protected|private|static|\s)*function\s+([A-Za-z_]\w*)\s*\(",
                re.MULTILINE,
            ),
            "method",
        ),
    ),
    re.compile(r"^\s*namespace\s+([\\\w]+)\s*;", re.MULTILINE),
)
_RUBY = _LanguageRules(
    _patterns(r"^\s*require(?:_relative)?\s+['\"]([^'\"]+)['\"]"),
    (
        (re.compile(r"^\s*(?:class|module)\s+([A-Za-z_]\w*)", re.MULTILINE), "class"),
        (re.compile(r"^\s*def\s+([A-Za-z_]\w*[!?=]?)", re.MULTILINE), "method"),
    ),
)
_C_FAMILY = _LanguageRules(
    _patterns(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]"),
    (
        (re.compile(r"^\s*(?:class|struct|enum)\s+([A-Za-z_]\w*)", re.MULTILINE), "class"),
        (
            re.compile(r"^\s*[\w:*&<>~]+\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", re.MULTILINE),
            "method",
        ),
    ),
)
_SWIFT_DART = _LanguageRules(
    _patterns(r"^\s*import\s+([\w.]+)"),
    (
        (
            re.compile(
                r"^\s*(?:public\s+|private\s+|final\s+)?(?:class|struct|protocol|enum|mixin)\s+([A-Za-z_]\w*)",
                re.MULTILINE,
            ),
            "class",
        ),
        (
            re.compile(
                r"^\s*(?:public\s+|private\s+|static\s+|async\s+)?func\s+([A-Za-z_]\w*)",
                re.MULTILINE,
            ),
            "method",
        ),
        (
            re.compile(
                r"^\s*(?:Future<[^>]+>\s+|void\s+|[A-Za-z_]\w*\s+)([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
                re.MULTILINE,
            ),
            "method",
        ),
    ),
)

_RULES: dict[str, _LanguageRules] = {
    ".py": _PYTHON,
    ".kt": _JVM,
    ".kts": _JVM,
    ".ts": _JS,
    ".tsx": _JS,
    ".js": _JS,
    ".jsx": _JS,
    ".mjs": _JS,
    ".cjs": _JS,
    ".cs": _CSHARP,
    ".go": _GO,
    ".rs": _RUST,
    ".php": _PHP,
    ".rb": _RUBY,
    ".c": _C_FAMILY,
    ".h": _C_FAMILY,
    ".cc": _C_FAMILY,
    ".cpp": _C_FAMILY,
    ".cxx": _C_FAMILY,
    ".hpp": _C_FAMILY,
    ".swift": _SWIFT_DART,
    ".dart": _SWIFT_DART,
}

_FRAMEWORK_HINTS = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "pytest": "pytest",
    "sqlalchemy": "sqlalchemy",
    "express": "express",
    "nestjs": "nestjs",
    "@nestjs": "nestjs",
    "react": "react",
    "next": "nextjs",
    "vue": "vue",
    "angular": "angular",
    "spring": "spring",
    "aspnet": "aspnet-core",
    "microsoft.aspnetcore": "aspnet-core",
    "gin-gonic": "gin",
    "fiber": "fiber",
    "actix": "actix",
    "rocket": "rocket",
    "rails": "rails",
    "laravel": "laravel",
    "flutter": "flutter",
}


class GenericParser:
    """Deterministic structural extraction for languages without a dedicated parser.

    It intentionally emits only syntax-level facts. Framework labels are import hints, not
    proof of framework behavior, and all resulting edges retain ``generic-regex`` evidence.
    """

    extensions = frozenset(_RULES)

    def analyze(self, path: str, text: str, digest: str) -> AnalysisResult:
        suffix = "." + path.rsplit(".", 1)[-1].casefold() if "." in path else ""
        rules = _RULES.get(suffix)
        lines = text.splitlines()
        file_node = GraphNode(
            f"file::{path}", "file", path.rsplit("/", 1)[-1], path, path, 1, max(1, len(lines))
        )
        if rules is None:
            return AnalysisResult(
                (file_node,),
                (),
                (Symbol(file_node, body_start_line=1, body_end_line=max(1, len(lines))),),
            )

        namespace_match = rules.namespace.search(text) if rules.namespace else None
        namespace = namespace_match.group(1) if namespace_match else ""
        imports = self._imports(rules, text)
        frameworks = _frameworks(imports, text)
        nodes: dict[str, GraphNode] = {file_node.node_id: file_node}
        edges: list[Edge] = []
        symbols: list[Symbol] = []
        for imported, line in imports:
            target = external_node("import", imported)
            nodes[target.node_id] = target
            edges.append(
                Edge(
                    file_node.node_id,
                    "IMPORTS",
                    target.node_id,
                    evidence(path, line, line, digest, "generic-regex"),
                    0.9,
                )
            )

        for regex, kind in rules.definitions:
            for match in regex.finditer(text):
                name = match.group(1)
                line = text.count("\n", 0, match.start()) + 1
                qname = f"{namespace}.{name}" if namespace else f"{path}::{name}"
                metadata = {
                    "language": suffix[1:],
                    "frameworks": frameworks,
                    "layer": _layer(name, frameworks, path),
                }
                node = GraphNode(
                    f"generic::{path}::{kind}::{name}",
                    kind,
                    name,
                    qname,
                    path,
                    line,
                    line,
                    metadata,
                )
                nodes[node.node_id] = node
                symbols.append(
                    Symbol(node, body_start_line=line, body_end_line=min(len(lines), line + 40))
                )
                edges.append(
                    Edge(
                        file_node.node_id,
                        "DEFINES",
                        node.node_id,
                        evidence(path, line, line, digest, "generic-regex"),
                        0.8,
                    )
                )
        if not symbols:
            symbols.append(Symbol(file_node, body_start_line=1, body_end_line=max(1, len(lines))))
        return AnalysisResult(tuple(nodes.values()), tuple(edges), tuple(symbols))

    @staticmethod
    def _imports(rules: _LanguageRules, text: str) -> list[tuple[str, int]]:
        found: dict[str, int] = {}
        for regex in rules.imports:
            for match in regex.finditer(text):
                value = match.group(1).strip().replace("::", ".")
                if value and value not in found:
                    found[value] = text.count("\n", 0, match.start()) + 1
        return [(name, line) for name, line in found.items()]


def _frameworks(imports: list[tuple[str, int]], text: str) -> list[str]:
    haystack = " ".join([*(name.casefold() for name, _ in imports), text[:4000].casefold()])
    return sorted({label for hint, label in _FRAMEWORK_HINTS.items() if hint in haystack})


def _layer(name: str, frameworks: list[str], path: str) -> str:
    lowered = f"{name} {path}".casefold()
    if "test" in lowered or any(value in frameworks for value in ("pytest",)):
        return "test"
    if any(value in lowered for value in ("controller", "handler", "route", "endpoint", "view")):
        return "controller"
    if any(value in lowered for value in ("repository", "store", "dao", "database")):
        return "repository"
    if any(value in lowered for value in ("service", "client", "manager")):
        return "service"
    return "domain"
