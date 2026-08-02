from __future__ import annotations

import hashlib
import re
from pathlib import Path

from athena.domain import Evidence, GraphNode

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "its",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "this",
    "to",
    "use",
    "we",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "you",
    "your",
    "add",
    "change",
    "create",
    "implement",
    "logic",
    "make",
    "please",
    "update",
}


def content_hash(content: str | bytes) -> str:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.blake2b(raw, digest_size=16).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    raw = "::".join(str(x) for x in parts)
    digest = hashlib.blake2b(raw.encode("utf-8"), digest_size=10).hexdigest()
    return f"{prefix}::{digest}"


def language_for(path: Path) -> str:
    return {
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".c": "c",
        ".h": "c-header",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp-header",
        ".swift": "swift",
        ".dart": "dart",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".properties": "properties",
        ".sql": "sql",
        ".md": "markdown",
    }.get(path.suffix.casefold(), "text")


def evidence(
    path: str, start: int, end: int, digest: str, extractor: str, confidence: float = 1.0
) -> Evidence:
    return Evidence(path, max(1, start), max(start, end), digest, extractor, confidence)


def external_node(kind: str, name: str) -> GraphNode:
    return GraphNode(
        node_id=f"external::{kind}::{name}",
        kind="external_symbol",
        name=name.rsplit(".", 1)[-1],
        qualified_name=name,
        metadata={"external_kind": kind},
    )


def search_terms(text: str) -> list[str]:
    raw = re.findall(r"[\w.$/-]+", text, flags=re.UNICODE)
    out: list[str] = []
    seen: set[str] = set()
    for value in raw:
        value = value.strip(".$/-")
        if not value:
            continue
        candidates = [value]
        candidates.extend(_CAMEL.sub(" ", value).split())
        if "." in value:
            candidates.extend(x for x in value.split(".") if x)
        for candidate in candidates:
            normalized = candidate.casefold()
            if len(normalized) < 2 or normalized in seen or normalized in _STOPWORDS:
                continue
            seen.add(normalized)
            out.append(candidate)
    return out


def exact_search_terms(text: str) -> list[str]:
    """Terms safe for exact graph seeding without broad camel-case expansion."""
    out: list[str] = []
    seen: set[str] = set()
    for value in re.findall(r"[\w.$/-]+", text, flags=re.UNICODE):
        value = value.strip(".$/-")
        normalized = value.casefold()
        if len(normalized) < 3 or normalized in _STOPWORDS or normalized in seen:
            continue
        seen.add(normalized)
        out.append(value)
    return out
