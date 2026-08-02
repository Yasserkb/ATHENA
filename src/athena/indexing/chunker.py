from __future__ import annotations

import re
from collections import defaultdict

from athena.domain import Chunk, Symbol
from athena.indexing.common import content_hash, stable_id


def build_chunks(
    path: str,
    text: str,
    language: str,
    symbols: tuple[Symbol, ...],
    chunk_lines: int,
    overlap_lines: int,
    tags: tuple[str, ...] = (),
) -> tuple[Chunk, ...]:
    lines = text.splitlines()
    if not lines:
        return ()
    if language == "markdown":
        return _build_markdown_chunks(path, lines, language, chunk_lines, overlap_lines, tags)
    chunks: list[Chunk] = []
    covered: set[int] = set()
    by_range: dict[tuple[int, int], list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        start = symbol.body_start_line or symbol.node.start_line
        end = symbol.body_end_line or symbol.node.end_line or start
        if start <= 0:
            continue
        end = min(max(start, end), len(lines))
        # Large methods/classes are split into bounded windows.
        cursor = start
        while cursor <= end:
            window_end = min(end, cursor + chunk_lines - 1)
            by_range[(cursor, window_end)].append(symbol)
            covered.update(range(cursor, window_end + 1))
            if window_end >= end:
                break
            cursor = max(cursor + 1, window_end - overlap_lines + 1)

    # Preserve module-level material and files with no detected symbols.
    cursor = 1
    while cursor <= len(lines):
        window_end = min(len(lines), cursor + chunk_lines - 1)
        uncovered = [line for line in range(cursor, window_end + 1) if line not in covered]
        if uncovered:
            start = min(uncovered)
            end = max(uncovered)
            by_range[(start, end)]
        if window_end >= len(lines):
            break
        cursor = max(cursor + 1, window_end - overlap_lines + 1)

    for (start, end), range_symbols in sorted(by_range.items()):
        content = "\n".join(lines[start - 1 : end])
        digest = content_hash(content)
        symbol_id = range_symbols[0].node.node_id if range_symbols else None
        symbol_tags = tuple(
            dict.fromkeys(
                [
                    *tags,
                    *(s.node.kind for s in range_symbols),
                    *(s.node.name for s in range_symbols),
                ]
            )
        )
        chunks.append(
            Chunk(
                chunk_id=stable_id("chunk", path, start, end, digest),
                path=path,
                start_line=start,
                end_line=end,
                content=content,
                content_hash=digest,
                symbol_id=symbol_id,
                language=language,
                tags=symbol_tags,
            )
        )
    return tuple(chunks)


def _build_markdown_chunks(
    path: str,
    lines: list[str],
    language: str,
    chunk_lines: int,
    overlap_lines: int,
    tags: tuple[str, ...],
) -> tuple[Chunk, ...]:
    """Chunk prose at Markdown heading boundaries before applying size windows.

    Long documents are commonly organized by headings. Keeping each heading with its
    following prose makes lexical retrieval return an interpretable section instead of
    an arbitrary fixed-line window. Every chunk still contains only original source
    lines and reports its exact range.
    """
    headings = [index + 1 for index, line in enumerate(lines) if re.match(r"^#{1,6}\s+\S", line)]
    starts = headings or [1]
    chunks: list[Chunk] = []
    for index, start in enumerate(starts):
        section_end = starts[index + 1] - 1 if index + 1 < len(starts) else len(lines)
        cursor = start
        while cursor <= section_end:
            end = min(section_end, cursor + chunk_lines - 1)
            content = "\n".join(lines[cursor - 1 : end])
            digest = content_hash(content)
            heading_tags = _markdown_heading_tags(lines[start - 1])
            chunks.append(
                Chunk(
                    chunk_id=stable_id("chunk", path, cursor, end, digest),
                    path=path,
                    start_line=cursor,
                    end_line=end,
                    content=content,
                    content_hash=digest,
                    language=language,
                    tags=tuple(dict.fromkeys([*tags, "markdown", *heading_tags])),
                )
            )
            if end >= section_end:
                break
            cursor = max(cursor + 1, end - overlap_lines + 1)
    return tuple(chunks)


def _markdown_heading_tags(line: str) -> tuple[str, ...]:
    """Produce compact lookup tags from one Markdown heading without storing prose metadata."""
    title = re.sub(r"^#{1,6}\s+", "", line).casefold()
    values = re.findall(r"[a-z0-9_+-]{2,}", title)
    return tuple(f"section:{value}" for value in values[:8])
