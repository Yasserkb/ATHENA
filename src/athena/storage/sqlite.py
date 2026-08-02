from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

from athena.cache import BoundedCache
from athena.domain import Chunk, Edge, FileRecord, GraphNode, IndexedFileAnalysis
from athena.errors import IndexCompatibilityError

_SCHEMA_VERSION = 2


def _http_contract_matches(provider: str, client: str) -> bool:
    try:
        provider_method, provider_route = provider.split(" ", 1)
        client_method, client_route = client.split(" ", 1)
    except ValueError:
        return False
    if provider_method not in {client_method, "any"}:
        return False
    provider_parts = provider_route.strip("/").split("/")
    client_parts = client_route.strip("/").split("/")
    return len(provider_parts) == len(client_parts) and all(
        expected == "{}" or expected == actual
        for expected, actual in zip(provider_parts, client_parts, strict=True)
    )


_SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    modified_ns INTEGER NOT NULL,
    language TEXT NOT NULL,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL DEFAULT '',
    simple_name TEXT NOT NULL DEFAULT '',
    qualified_name TEXT NOT NULL,
    qualified_name_normalized TEXT NOT NULL DEFAULT '',
    path TEXT,
    path_normalized TEXT NOT NULL DEFAULT '',
    package_name TEXT NOT NULL DEFAULT '',
    start_line INTEGER NOT NULL DEFAULT 0,
    end_line INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_qname ON nodes(qualified_name);
CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);

CREATE TABLE IF NOT EXISTS edges (
    source_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    target_id TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    extractor TEXT NOT NULL,
    confidence REAL NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY(source_id, relation, target_id, evidence_path, start_line),
    FOREIGN KEY(source_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id, relation);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id, relation);
CREATE INDEX IF NOT EXISTS idx_edges_evidence ON edges(evidence_path);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    symbol_id TEXT,
    language TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(symbol_id) REFERENCES nodes(node_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path, start_line);
CREATE INDEX IF NOT EXISTS idx_chunks_symbol ON chunks(symbol_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    path,
    symbol,
    tags,
    content,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operation TEXT NOT NULL,
    repository TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    result_count INTEGER NOT NULL DEFAULT 0,
    payload TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_metrics_repo ON metrics(repository, created_at);
"""


class SQLiteStore:
    def __init__(self, path: Path, cache_max_entries: int = 256) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA busy_timeout = 5000")
        self.db.executescript(_SCHEMA)
        self._validate_schema()
        self._ensure_search_schema()
        self.db.execute(
            "INSERT OR IGNORE INTO metadata(key, value) VALUES('index_generation', '0')"
        )
        self.db.commit()
        self._observed_generation = self._read_index_generation()
        self._exact_cache: BoundedCache[tuple[object, ...], tuple[tuple[GraphNode, float], ...]] = (
            BoundedCache(cache_max_entries)
        )
        self._lexical_cache: BoundedCache[tuple[object, ...], tuple[tuple[Chunk, float], ...]] = (
            BoundedCache(cache_max_entries)
        )
        self._graph_cache: BoundedCache[
            tuple[object, ...], tuple[tuple[GraphNode, int, str], ...]
        ] = BoundedCache(cache_max_entries)

    def _validate_schema(self) -> None:
        row = self.db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if row is None:
            self.db.execute(
                "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                (str(_SCHEMA_VERSION),),
            )
            self.db.commit()
            return
        version = int(row["value"])
        if version == 1:
            self._migrate_v1_to_v2()
            return
        if version != _SCHEMA_VERSION:
            raise IndexCompatibilityError(
                f"Index schema {row['value']} is incompatible with runtime schema {_SCHEMA_VERSION}. "
                "Delete or migrate the index before continuing."
            )

    def _migrate_v1_to_v2(self) -> None:
        with self.transaction():
            for definition in (
                "name_normalized TEXT NOT NULL DEFAULT ''",
                "simple_name TEXT NOT NULL DEFAULT ''",
                "qualified_name_normalized TEXT NOT NULL DEFAULT ''",
                "path_normalized TEXT NOT NULL DEFAULT ''",
                "package_name TEXT NOT NULL DEFAULT ''",
            ):
                self.db.execute(f"ALTER TABLE nodes ADD COLUMN {definition}")
            rows = tuple(
                self.db.execute("SELECT node_id, kind, name, qualified_name, path FROM nodes")
            )
            self.db.executemany(
                """UPDATE nodes SET
                   name_normalized=?,
                   simple_name=?,
                   qualified_name_normalized=?,
                   path_normalized=?,
                   package_name=?
                   WHERE node_id=?""",
                (
                    (
                        str(row["name"]).casefold(),
                        str(row["name"]).casefold(),
                        str(row["qualified_name"]).casefold(),
                        str(row["path"] or "").casefold(),
                        _package_name(str(row["qualified_name"]), str(row["kind"])),
                        str(row["node_id"]),
                    )
                    for row in rows
                ),
            )
            self.db.execute(
                "UPDATE metadata SET value=? WHERE key='schema_version'",
                (str(_SCHEMA_VERSION),),
            )

    def _ensure_search_schema(self) -> None:
        self.db.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_nodes_name_normalized
                ON nodes(name_normalized);
            CREATE INDEX IF NOT EXISTS idx_nodes_simple_name
                ON nodes(simple_name);
            CREATE INDEX IF NOT EXISTS idx_nodes_qname_normalized
                ON nodes(qualified_name_normalized);
            CREATE INDEX IF NOT EXISTS idx_nodes_path_normalized
                ON nodes(path_normalized);
            CREATE INDEX IF NOT EXISTS idx_nodes_package_name
                ON nodes(package_name);
            CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                node_id UNINDEXED,
                name,
                qualified_name,
                path,
                kind,
                metadata,
                tokenize='unicode61 remove_diacritics 2'
            );
            """
        )
        count = int(self.db.execute("SELECT COUNT(*) FROM nodes_fts").fetchone()[0])
        node_count = int(self.db.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
        if count != node_count:
            self._rebuild_node_fts()
        self.db.commit()

    def _rebuild_node_fts(self) -> None:
        self.db.execute("DELETE FROM nodes_fts")
        self.db.execute(
            """INSERT INTO nodes_fts(node_id,name,qualified_name,path,kind,metadata)
               SELECT node_id,name,qualified_name,COALESCE(path,''),kind,metadata FROM nodes"""
        )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.db.execute("BEGIN IMMEDIATE")
            yield self.db
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> SQLiteStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def set_metadata(self, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO metadata(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.db.commit()

    def metadata(self) -> dict[str, str]:
        return {
            row["key"]: row["value"] for row in self.db.execute("SELECT key, value FROM metadata")
        }

    def index_generation(self) -> int:
        current = self._read_index_generation()
        if current != self._observed_generation:
            self._exact_cache.invalidate()
            self._lexical_cache.invalidate()
            self._graph_cache.invalidate()
            self._observed_generation = current
        return current

    def _read_index_generation(self) -> int:
        row = self.db.execute("SELECT value FROM metadata WHERE key='index_generation'").fetchone()
        return int(row["value"]) if row is not None else 0

    def _bump_index_generation(self) -> None:
        self.db.execute(
            """INSERT INTO metadata(key, value) VALUES('index_generation', '1')
               ON CONFLICT(key) DO UPDATE
               SET value=CAST(metadata.value AS INTEGER) + 1"""
        )

    def cache_status(self) -> dict[str, dict[str, int | float]]:
        self.index_generation()
        return {
            "exact_nodes": self._exact_cache.stats().to_dict(),
            "lexical_chunks": self._lexical_cache.stats().to_dict(),
            "graph_walk": self._graph_cache.stats().to_dict(),
        }

    def clear_caches(self) -> None:
        self._exact_cache.invalidate()
        self._lexical_cache.invalidate()
        self._graph_cache.invalidate()

    def file_state(self, path: str) -> sqlite3.Row | None:
        return cast(
            sqlite3.Row | None,
            self.db.execute(
                "SELECT path, content_hash, size_bytes, modified_ns, language FROM files WHERE path=?",
                (path,),
            ).fetchone(),
        )

    def indexed_paths(self) -> set[str]:
        return {row["path"] for row in self.db.execute("SELECT path FROM files")}

    def delete_file(self, path: str) -> None:
        with self.transaction():
            self._delete_file(path)
            self._bump_index_generation()

    def delete_files(self, paths: Sequence[str]) -> None:
        if not paths:
            return
        with self.transaction():
            for path in paths:
                self._delete_file(path)
            self._bump_index_generation()

    def _delete_file(self, path: str) -> None:
        node_ids = [
            str(row["node_id"])
            for row in self.db.execute("SELECT node_id FROM nodes WHERE path=?", (path,))
        ]
        chunk_ids = [
            row["chunk_id"]
            for row in self.db.execute("SELECT chunk_id FROM chunks WHERE path=?", (path,))
        ]
        if chunk_ids:
            self.db.executemany(
                "DELETE FROM chunks_fts WHERE chunk_id=?", ((x,) for x in chunk_ids)
            )
        self.db.execute("DELETE FROM chunks WHERE path=?", (path,))
        self.db.execute("DELETE FROM edges WHERE evidence_path=?", (path,))
        self.db.execute("DELETE FROM nodes WHERE path=?", (path,))
        self._delete_node_fts(node_ids)
        self.db.execute("DELETE FROM files WHERE path=?", (path,))

    def replace_file_analyses(
        self,
        analyses: Sequence[IndexedFileAnalysis],
        metadata_updates: Sequence[FileRecord] = (),
    ) -> None:
        if not analyses and not metadata_updates:
            return
        with self.transaction():
            for item in analyses:
                self._delete_file(item.file.path)
            self.db.executemany(
                """INSERT INTO files(path, content_hash, size_bytes, modified_ns, language)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(path) DO UPDATE SET
                     content_hash=excluded.content_hash,
                     size_bytes=excluded.size_bytes,
                     modified_ns=excluded.modified_ns,
                     language=excluded.language,
                     indexed_at=CURRENT_TIMESTAMP""",
                (
                    (
                        item.file.path,
                        item.file.content_hash,
                        item.file.size_bytes,
                        item.file.modified_ns,
                        item.file.language,
                    )
                    for item in analyses
                ),
            )
            if analyses:
                self._bump_index_generation()
            self._insert_nodes(tuple(node for item in analyses for node in item.nodes))
            self._insert_edges(tuple(edge for item in analyses for edge in item.edges))
            self._insert_chunks(tuple(chunk for item in analyses for chunk in item.chunks))
            self.db.executemany(
                """UPDATE files
                   SET size_bytes=?, modified_ns=?, language=?, indexed_at=CURRENT_TIMESTAMP
                   WHERE path=? AND content_hash=?""",
                (
                    (
                        record.size_bytes,
                        record.modified_ns,
                        record.language,
                        record.path,
                        record.content_hash,
                    )
                    for record in metadata_updates
                ),
            )

    def replace_file_analysis(
        self,
        file: FileRecord,
        nodes: Sequence[GraphNode],
        edges: Sequence[Edge],
        chunks: Sequence[Chunk],
    ) -> None:
        self.replace_file_analyses(
            (IndexedFileAnalysis(file, tuple(nodes), tuple(edges), tuple(chunks)),)
        )

    def replace_persona_graph(self, nodes: Sequence[GraphNode], edges: Sequence[Edge]) -> None:
        with self.transaction():
            node_ids = [
                str(row["node_id"])
                for row in self.db.execute("SELECT node_id FROM nodes WHERE path='@persona'")
            ]
            self.db.execute("DELETE FROM edges WHERE evidence_path='@persona'")
            self.db.execute("DELETE FROM nodes WHERE path='@persona'")
            self._delete_node_fts(node_ids)
            self._insert_nodes(nodes)
            self._insert_edges(edges)
            self._bump_index_generation()

    def replace_derived_graph(self, nodes: Sequence[GraphNode], edges: Sequence[Edge]) -> None:
        with self.transaction():
            node_ids = [
                str(row["node_id"])
                for row in self.db.execute("SELECT node_id FROM nodes WHERE path LIKE '@derived%'")
            ]
            self.db.execute("DELETE FROM edges WHERE evidence_path LIKE '@derived%'")
            self.db.execute("DELETE FROM nodes WHERE path LIKE '@derived%'")
            self._delete_node_fts(node_ids)
            self._insert_nodes(nodes)
            self._insert_edges(edges)
            self._bump_index_generation()

    def replace_derived_graph_for_paths(
        self, paths: Sequence[str], nodes: Sequence[GraphNode], edges: Sequence[Edge]
    ) -> None:
        owners = tuple(f"@derived:{path}" for path in paths)
        if not owners and not nodes and not edges:
            return
        with self.transaction():
            if owners:
                placeholders = ",".join("?" for _ in owners)
                node_ids = [
                    str(row["node_id"])
                    for row in self.db.execute(
                        f"SELECT node_id FROM nodes WHERE path IN ({placeholders})", owners
                    )
                ]
                self.db.execute(
                    f"DELETE FROM edges WHERE evidence_path IN ({placeholders})", owners
                )
                self.db.execute(f"DELETE FROM nodes WHERE path IN ({placeholders})", owners)
                self._delete_node_fts(node_ids)
            self._insert_nodes(nodes)
            self._insert_edges(edges)
            self._bump_index_generation()

    def nodes_for_paths(self, paths: Sequence[str]) -> list[GraphNode]:
        if not paths:
            return []
        placeholders = ",".join("?" for _ in paths)
        return [
            self._row_to_node(row)
            for row in self.db.execute(
                f"SELECT * FROM nodes WHERE path IN ({placeholders})", tuple(paths)
            )
        ]

    def edges_for_evidence_paths(self, paths: Sequence[str]) -> list[dict[str, Any]]:
        if not paths:
            return []
        placeholders = ",".join("?" for _ in paths)
        return [
            dict(row)
            for row in self.db.execute(
                f"SELECT * FROM edges WHERE evidence_path IN ({placeholders})", tuple(paths)
            )
        ]

    def node_by_id(self, node_id: str) -> GraphNode | None:
        row = self.db.execute("SELECT * FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        return self._row_to_node(row) if row is not None else None

    def resolve_repository_node(self, qualified_name: str, relation: str) -> GraphNode | None:
        raw = qualified_name.casefold()
        if relation == "CALLS" and "#" in raw:
            owner, method = raw.split("#", 1)
            rows = list(
                self.db.execute(
                    """SELECT * FROM nodes
                       WHERE kind='method'
                         AND qualified_name_normalized GLOB ?
                         AND simple_name=?
                       LIMIT 2""",
                    (owner + "#*", method),
                )
            )
            if len(rows) == 1:
                return self._row_to_node(rows[0])
            raw = owner
        rows = list(
            self.db.execute(
                """SELECT * FROM nodes
                   WHERE kind!='external_symbol'
                     AND qualified_name_normalized=?
                   LIMIT 2""",
                (raw,),
            )
        )
        if len(rows) == 1:
            return self._row_to_node(rows[0])
        if relation == "CALLS_ENDPOINT":
            rows = list(
                self.db.execute(
                    """SELECT * FROM nodes
                       WHERE kind='endpoint'
                         AND qualified_name_normalized GLOB ?
                       LIMIT 100""",
                    (raw.split(" ", 1)[0] + " *",),
                )
            )
            matches = [
                row
                for row in rows
                if _http_contract_matches(str(row["qualified_name_normalized"]), raw)
            ]
            if len(matches) == 1:
                return self._row_to_node(matches[0])
            return None
        simple = raw.rsplit(".", 1)[-1].split("#", 1)[0]
        rows = list(
            self.db.execute(
                """SELECT * FROM nodes
                   WHERE kind NOT IN ('external_symbol','file','package')
                     AND simple_name=?
                   LIMIT 2""",
                (simple,),
            )
        )
        return self._row_to_node(rows[0]) if len(rows) == 1 else None

    def derived_owner_paths_touching(self, paths: Sequence[str]) -> set[str]:
        if not paths:
            return set()
        placeholders = ",".join("?" for _ in paths)
        rows = self.db.execute(
            f"""SELECT DISTINCT e.evidence_path
                FROM edges e
                LEFT JOIN nodes s ON s.node_id=e.source_id
                LEFT JOIN nodes t ON t.node_id=e.target_id
                WHERE e.evidence_path LIKE '@derived:%'
                  AND (s.path IN ({placeholders}) OR t.path IN ({placeholders}))""",
            (*paths, *paths),
        )
        return {
            str(row["evidence_path"])[len("@derived:") :]
            for row in rows
            if str(row["evidence_path"]).startswith("@derived:")
        }

    def reference_owner_paths_for(self, paths: Sequence[str]) -> set[str]:
        if not paths:
            return set()
        placeholders = ",".join("?" for _ in paths)
        rows = self.db.execute(
            f"""SELECT DISTINCT source.path
                FROM nodes changed
                JOIN nodes external
                  ON external.kind='external_symbol'
                 AND (external.qualified_name=changed.qualified_name
                      OR external.name=changed.name)
                JOIN edges e ON e.target_id=external.node_id
                JOIN nodes source ON source.node_id=e.source_id
                WHERE changed.path IN ({placeholders})
                  AND source.path IS NOT NULL
                  AND source.path NOT LIKE '@%'""",
            tuple(paths),
        )
        owners = {str(row["path"]) for row in rows}
        changed_endpoint = self.db.execute(
            f"""SELECT 1 FROM nodes
                WHERE path IN ({placeholders}) AND kind='endpoint'
                LIMIT 1""",
            tuple(paths),
        ).fetchone()
        if changed_endpoint is not None:
            owners.update(
                str(row["path"])
                for row in self.db.execute(
                    """SELECT DISTINCT source.path
                       FROM edges e
                       JOIN nodes source ON source.node_id=e.source_id
                       JOIN nodes target ON target.node_id=e.target_id
                       WHERE e.relation='CALLS_ENDPOINT'
                         AND target.kind='external_symbol'
                         AND source.path IS NOT NULL"""
                )
            )
        return owners

    def cleanup_orphan_external_nodes(self) -> int:
        with self.transaction():
            node_ids = [
                str(row["node_id"])
                for row in self.db.execute(
                    """SELECT node_id FROM nodes
                       WHERE kind='external_symbol'
                         AND NOT EXISTS (SELECT 1 FROM edges WHERE source_id=nodes.node_id)
                         AND NOT EXISTS (SELECT 1 FROM edges WHERE target_id=nodes.node_id)"""
                )
            ]
            cursor = self.db.execute(
                """DELETE FROM nodes
                   WHERE kind='external_symbol'
                     AND NOT EXISTS (SELECT 1 FROM edges WHERE source_id=nodes.node_id)
                     AND NOT EXISTS (SELECT 1 FROM edges WHERE target_id=nodes.node_id)"""
            )
            self._delete_node_fts(node_ids)
            if node_ids:
                self._bump_index_generation()
            return int(cursor.rowcount if cursor.rowcount >= 0 else 0)

    def all_nodes(self) -> list[GraphNode]:
        return [self._row_to_node(row) for row in self.db.execute("SELECT * FROM nodes")]

    def all_edges(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM edges")]

    def upsert_global_nodes(self, nodes: Sequence[GraphNode]) -> None:
        if not nodes:
            return
        with self.transaction():
            self._insert_nodes(nodes)
            self._bump_index_generation()

    def upsert_global_edges(self, edges: Sequence[Edge]) -> None:
        if not edges:
            return
        with self.transaction():
            self._insert_edges(edges)
            self._bump_index_generation()

    def _insert_nodes(self, nodes: Sequence[GraphNode]) -> None:
        nodes = tuple(nodes)
        if not nodes:
            return
        self.db.executemany(
            """INSERT INTO nodes(node_id, kind, name, name_normalized, simple_name,
                                  qualified_name, qualified_name_normalized, path,
                                  path_normalized, package_name, start_line, end_line, metadata)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(node_id) DO UPDATE SET
                 kind=excluded.kind, name=excluded.name,
                 name_normalized=excluded.name_normalized,
                 simple_name=excluded.simple_name,
                 qualified_name=excluded.qualified_name,
                 qualified_name_normalized=excluded.qualified_name_normalized,
                 path=COALESCE(excluded.path, nodes.path),
                 path_normalized=CASE WHEN excluded.path!='' THEN excluded.path_normalized
                                      ELSE nodes.path_normalized END,
                 package_name=excluded.package_name,
                 start_line=CASE WHEN excluded.start_line > 0 THEN excluded.start_line ELSE nodes.start_line END,
                 end_line=CASE WHEN excluded.end_line > 0 THEN excluded.end_line ELSE nodes.end_line END,
                 metadata=excluded.metadata""",
            (
                (
                    n.node_id,
                    n.kind,
                    n.name,
                    n.name.casefold(),
                    n.name.casefold(),
                    n.qualified_name,
                    n.qualified_name.casefold(),
                    n.path,
                    (n.path or "").casefold(),
                    _package_name(n.qualified_name, n.kind),
                    n.start_line,
                    n.end_line,
                    json.dumps(n.metadata, sort_keys=True),
                )
                for n in nodes
            ),
        )
        self._delete_node_fts([node.node_id for node in nodes])
        self.db.executemany(
            """INSERT INTO nodes_fts(node_id,name,qualified_name,path,kind,metadata)
               VALUES(?,?,?,?,?,?)""",
            (
                (
                    node.node_id,
                    node.name,
                    node.qualified_name,
                    node.path or "",
                    node.kind,
                    json.dumps(node.metadata, sort_keys=True),
                )
                for node in nodes
            ),
        )

    def _delete_node_fts(self, node_ids: Sequence[str]) -> None:
        if node_ids:
            self.db.executemany("DELETE FROM nodes_fts WHERE node_id=?", ((x,) for x in node_ids))

    def _insert_edges(self, edges: Sequence[Edge]) -> None:
        self.db.executemany(
            """INSERT INTO edges(source_id, relation, target_id, evidence_path,
                                  start_line, end_line, content_hash, extractor,
                                  confidence, metadata)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_id, relation, target_id, evidence_path, start_line)
               DO UPDATE SET end_line=excluded.end_line,
                             content_hash=excluded.content_hash,
                             extractor=excluded.extractor,
                             confidence=excluded.confidence,
                             metadata=excluded.metadata""",
            (
                (
                    e.source_id,
                    e.relation,
                    e.target_id,
                    e.evidence.path,
                    e.evidence.start_line,
                    e.evidence.end_line,
                    e.evidence.content_hash,
                    e.evidence.extractor,
                    e.confidence,
                    json.dumps(e.metadata, sort_keys=True),
                )
                for e in edges
            ),
        )

    def _insert_chunks(self, chunks: Sequence[Chunk]) -> None:
        self.db.executemany(
            """INSERT INTO chunks(chunk_id, path, start_line, end_line, content,
                                   content_hash, symbol_id, language, tags)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                (
                    c.chunk_id,
                    c.path,
                    c.start_line,
                    c.end_line,
                    c.content,
                    c.content_hash,
                    c.symbol_id,
                    c.language,
                    json.dumps(c.tags),
                )
                for c in chunks
            ),
        )
        symbol_names = (
            {
                row["node_id"]: row["qualified_name"]
                for row in self.db.execute(
                    "SELECT node_id, qualified_name FROM nodes WHERE node_id IN "
                    f"({','.join('?' for _ in {c.symbol_id for c in chunks if c.symbol_id})})",
                    tuple({c.symbol_id for c in chunks if c.symbol_id}),
                )
            }
            if any(c.symbol_id for c in chunks)
            else {}
        )
        self.db.executemany(
            "INSERT INTO chunks_fts(chunk_id, path, symbol, tags, content) VALUES(?,?,?,?,?)",
            (
                (
                    c.chunk_id,
                    c.path,
                    symbol_names.get(c.symbol_id or "", ""),
                    " ".join(c.tags),
                    c.content,
                )
                for c in chunks
            ),
        )

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row) -> Chunk:
        return Chunk(
            chunk_id=row["chunk_id"],
            path=row["path"],
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
            content=row["content"],
            content_hash=row["content_hash"],
            symbol_id=row["symbol_id"],
            language=row["language"],
            tags=tuple(json.loads(row["tags"] or "[]")),
        )

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> GraphNode:
        return GraphNode(
            node_id=row["node_id"],
            kind=row["kind"],
            name=row["name"],
            qualified_name=row["qualified_name"],
            path=row["path"],
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def exact_nodes(self, terms: Sequence[str], limit: int = 20) -> list[tuple[GraphNode, float]]:
        generation = self.index_generation()
        key = (generation, tuple(terms), limit)
        result = self._exact_cache.get_or_compute(
            key, lambda: tuple(self._exact_nodes_uncached(terms, limit))
        )
        return list(result)

    def _exact_nodes_uncached(
        self, terms: Sequence[str], limit: int = 20
    ) -> list[tuple[GraphNode, float]]:
        if not terms:
            return []
        scored: dict[str, tuple[GraphNode, float]] = {}
        for term in terms:
            normalized = _normalize_search(term)
            if not normalized:
                continue
            rows = self.db.execute(
                """SELECT *,
                          CASE
                            WHEN name_normalized=? OR qualified_name_normalized=? THEN 1.0
                            WHEN simple_name=? THEN 0.95
                            WHEN name_normalized GLOB ? THEN 0.85
                            WHEN qualified_name_normalized GLOB ? THEN 0.8
                            ELSE 0.72
                          END AS search_score
                   FROM nodes
                   WHERE name_normalized=?
                      OR qualified_name_normalized=?
                      OR simple_name=?
                      OR name_normalized GLOB ?
                      OR qualified_name_normalized GLOB ?
                      OR path_normalized GLOB ?
                   ORDER BY search_score DESC, qualified_name
                   LIMIT ?""",
                (
                    normalized,
                    normalized,
                    normalized,
                    normalized + "*",
                    normalized + "*",
                    normalized,
                    normalized,
                    normalized,
                    normalized + "*",
                    normalized + "*",
                    normalized + "*",
                    limit,
                ),
            )
            for row in rows:
                node = self._row_to_node(row)
                score = float(row["search_score"])
                previous = scored.get(node.node_id)
                if previous is None or score > previous[1]:
                    scored[node.node_id] = (node, score)

            tokens = [token for token in _fts_tokens(term) if len(token) > 1]
            if tokens and len(scored) < limit:
                expression = " OR ".join(f'"{token}"*' for token in tokens[:20])
                fts_rows = self.db.execute(
                    """SELECT n.*, bm25(nodes_fts, 0.0, 2.0, 1.5, 0.8, 0.4, 0.2) AS rank
                       FROM nodes_fts
                       JOIN nodes n ON n.node_id=nodes_fts.node_id
                       WHERE nodes_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (expression, limit),
                )
                for row in fts_rows:
                    node = self._row_to_node(row)
                    rank = abs(float(row["rank"]))
                    score = 0.6 + (0.1 * rank / (1.0 + rank))
                    previous = scored.get(node.node_id)
                    if previous is None or score > previous[1]:
                        scored[node.node_id] = (node, score)
        return sorted(scored.values(), key=lambda item: item[1], reverse=True)[:limit]

    def lexical_chunks(self, query: str, limit: int = 20) -> list[tuple[Chunk, float]]:
        generation = self.index_generation()
        key = (generation, query, limit)
        result = self._lexical_cache.get_or_compute(
            key, lambda: tuple(self._lexical_chunks_uncached(query, limit))
        )
        return list(result)

    def _lexical_chunks_uncached(self, query: str, limit: int = 20) -> list[tuple[Chunk, float]]:
        tokens = [token for token in _fts_tokens(query) if len(token) > 1]
        if not tokens:
            return []
        expression = " OR ".join(f'"{token}"' for token in tokens[:20])
        rows = self.db.execute(
            """SELECT c.*, bm25(chunks_fts, 0.0, 1.8, 1.2, 0.5, 1.0) AS rank
               FROM chunks_fts
               JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
               WHERE chunks_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (expression, limit),
        )
        out: list[tuple[Chunk, float]] = []
        for row in rows:
            # FTS5 bm25 is lower-is-better and commonly negative. Normalize monotonically.
            rank = abs(float(row["rank"]))
            score = rank / (1.0 + rank)
            out.append((self._row_to_chunk(row), score))
        return out

    def chunks_for_nodes(self, node_ids: Sequence[str], limit: int = 80) -> list[Chunk]:
        if not node_ids:
            return []
        placeholders = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"""SELECT DISTINCT c.* FROM chunks c
                LEFT JOIN nodes n ON n.node_id=c.symbol_id
                WHERE c.symbol_id IN ({placeholders})
                   OR c.path IN (SELECT path FROM nodes WHERE node_id IN ({placeholders}))
                ORDER BY c.path, c.start_line LIMIT ?""",
            (*node_ids, *node_ids, limit),
        )
        return [self._row_to_chunk(row) for row in rows]

    def graph_walk(
        self,
        start_ids: Sequence[str],
        relations: Sequence[str],
        depth: int,
        max_nodes: int,
    ) -> list[tuple[GraphNode, int, str]]:
        generation = self.index_generation()
        key = (generation, tuple(start_ids), tuple(relations), depth, max_nodes)
        result = self._graph_cache.get_or_compute(
            key,
            lambda: tuple(self._graph_walk_uncached(start_ids, relations, depth, max_nodes)),
        )
        return list(result)

    def _graph_walk_uncached(
        self,
        start_ids: Sequence[str],
        relations: Sequence[str],
        depth: int,
        max_nodes: int,
    ) -> list[tuple[GraphNode, int, str]]:
        if not start_ids or depth <= 0:
            return []
        allowed = set(relations)
        visited = set(start_ids)
        frontier = list(dict.fromkeys(start_ids))
        found: list[tuple[GraphNode, int, str]] = []
        for distance in range(1, depth + 1):
            if not frontier or len(found) >= max_nodes:
                break
            placeholders = ",".join("?" for _ in frontier)
            relation_clause = ""
            relation_params: tuple[str, ...] = ()
            if allowed:
                relation_placeholders = ",".join("?" for _ in allowed)
                relation_clause = f" AND relation IN ({relation_placeholders})"
                relation_params = tuple(sorted(allowed))
            rows = self.db.execute(
                f"""SELECT relation, source_id, target_id
                    FROM edges
                    WHERE (source_id IN ({placeholders})
                           OR target_id IN ({placeholders}))
                    {relation_clause}
                    ORDER BY relation, source_id, target_id""",
                (*frontier, *frontier, *relation_params),
            )
            frontier_set = set(frontier)
            candidates: dict[str, str] = {}
            for row in rows:
                source_id = str(row["source_id"])
                target_id = str(row["target_id"])
                other = target_id if source_id in frontier_set else source_id
                if other not in visited:
                    candidates.setdefault(other, str(row["relation"]))
            remaining = max_nodes - len(found)
            candidate_ids = list(candidates)[:remaining]
            if not candidate_ids:
                break
            candidate_placeholders = ",".join("?" for _ in candidate_ids)
            node_rows = {
                str(row["node_id"]): row
                for row in self.db.execute(
                    f"SELECT * FROM nodes WHERE node_id IN ({candidate_placeholders})",
                    tuple(candidate_ids),
                )
            }
            frontier = []
            for node_id in candidate_ids:
                node_row = node_rows.get(node_id)
                if node_row is None:
                    continue
                visited.add(node_id)
                frontier.append(node_id)
                found.append((self._row_to_node(node_row), distance, candidates[node_id]))
        return found

    def node_neighbors(self, name: str, limit: int = 50) -> list[dict[str, Any]]:
        seeds = self.exact_nodes([name], limit=10)
        if not seeds:
            return []
        ids = [node.node_id for node, _ in seeds]
        placeholders = ",".join("?" for _ in ids)
        rows = self.db.execute(
            f"""SELECT e.relation, e.source_id, e.target_id, e.evidence_path,
                       e.start_line, e.end_line, e.confidence,
                       s.qualified_name AS source_name, t.qualified_name AS target_name
                FROM edges e
                JOIN nodes s ON s.node_id=e.source_id
                JOIN nodes t ON t.node_id=e.target_id
                WHERE e.source_id IN ({placeholders}) OR e.target_id IN ({placeholders})
                ORDER BY e.confidence DESC, e.relation
                LIMIT ?""",
            (*ids, *ids, limit),
        )
        return [dict(row) for row in rows]

    def architecture_lines(self, node_ids: Sequence[str], limit: int = 20) -> list[str]:
        if not node_ids:
            return []
        placeholders = ",".join("?" for _ in node_ids)
        rows = self.db.execute(
            f"""SELECT DISTINCT s.qualified_name source_name, e.relation,
                                t.qualified_name target_name
                FROM edges e
                JOIN nodes s ON s.node_id=e.source_id
                JOIN nodes t ON t.node_id=e.target_id
                WHERE e.source_id IN ({placeholders}) OR e.target_id IN ({placeholders})
                ORDER BY e.confidence DESC LIMIT ?""",
            (*node_ids, *node_ids, limit),
        )
        return [f"{row['source_name']} --{row['relation']}--> {row['target_name']}" for row in rows]

    def stats(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for table in ("files", "nodes", "edges", "chunks"):
            row = self.db.execute(f"SELECT COUNT(*) count FROM {table}").fetchone()
            result[table] = int(row["count"])
        return result

    def repository_token_estimate(self) -> int:
        """Estimate the tokens required to submit every indexed source file once.

        File sizes avoid double-counting overlap between adjacent chunks. The divisor matches
        Athena's provider-neutral UTF-8 token estimator.
        """
        row = self.db.execute("SELECT COALESCE(SUM(size_bytes), 0) bytes FROM files").fetchone()
        size_bytes = int(row["bytes"] or 0)
        return math.ceil(size_bytes / 3.6) if size_bytes else 0

    def observatory_metrics(
        self, repository: str | None = None, limit: int = 30
    ) -> dict[str, Any]:
        """Return bounded activity and token-efficiency data for the local Observatory."""
        where = " WHERE repository=?" if repository else ""
        params: tuple[Any, ...] = (repository,) if repository else ()
        rows = list(
            self.db.execute(
                f"SELECT created_at, operation, repository, duration_ms, estimated_tokens, "
                f"result_count, payload FROM metrics{where} ORDER BY id DESC",
                params,
            )
        )
        current_baseline = self.repository_token_estimate()
        context_rows: list[dict[str, Any]] = []
        delivered = 0
        baseline = 0
        cache_hits = 0
        confidence_total = 0.0
        confidence_samples = 0
        for row in rows:
            if row["operation"] != "context":
                continue
            payload = json.loads(row["payload"] or "{}")
            used = int(row["estimated_tokens"] or 0)
            request_baseline = int(payload.get("repository_token_estimate") or current_baseline)
            avoided = int(
                payload.get("estimated_tokens_avoided") or max(0, request_baseline - used)
            )
            delivered += used
            baseline += request_baseline
            cache_hits += int(bool(payload.get("cache_hit")))
            if payload.get("confidence") is not None:
                confidence_total += float(payload["confidence"])
                confidence_samples += 1
            context_rows.append(
                {
                    "created_at": row["created_at"],
                    "duration_ms": round(float(row["duration_ms"]), 2),
                    "tokens_delivered": used,
                    "baseline_tokens": request_baseline,
                    "tokens_avoided": avoided,
                    "result_count": int(row["result_count"]),
                    "persona": payload.get("persona", "auto"),
                    "confidence": payload.get("confidence"),
                    "cache_hit": bool(payload.get("cache_hit")),
                    "selected_evidence": payload.get("selected_evidence", []),
                    "architecture": payload.get("architecture", []),
                    "tokenizer": payload.get("tokenizer"),
                    "token_count_source": payload.get("token_count_source"),
                }
            )
        avoided_total = max(0, baseline - delivered)
        request_count = len(context_rows)
        recent_rows = rows[: max(1, limit)]
        return {
            "savings": {
                "context_requests": request_count,
                "repository_token_estimate": current_baseline,
                "baseline_tokens": baseline,
                "tokens_delivered": delivered,
                "tokens_avoided": avoided_total,
                "savings_rate": round(avoided_total / baseline, 4) if baseline else 0.0,
                "cache_hits": cache_hits,
                "cache_hit_rate": round(cache_hits / request_count, 4) if request_count else 0.0,
                "average_confidence": (
                    round(confidence_total / confidence_samples, 3)
                    if confidence_samples
                    else 0.0
                ),
                "baseline": "full-index-per-context-request",
                "measurement": "estimated:utf8-bytes-v1",
            },
            "contexts": context_rows[: max(1, limit)],
            "recent": [
                {
                    "created_at": row["created_at"],
                    "operation": row["operation"],
                    "duration_ms": round(float(row["duration_ms"]), 2),
                    "estimated_tokens": int(row["estimated_tokens"]),
                    "result_count": int(row["result_count"]),
                    "payload": json.loads(row["payload"] or "{}"),
                }
                for row in recent_rows
            ],
        }

    def graph_overview(self, limit: int = 48) -> dict[str, Any]:
        """Return a bounded graph centered on the most connected code nodes."""
        rows = list(
            self.db.execute(
                """SELECT n.*, COUNT(d.node_id) AS degree
                   FROM nodes n
                   LEFT JOIN (
                       SELECT source_id AS node_id FROM edges
                       UNION ALL
                       SELECT target_id AS node_id FROM edges
                   ) d ON d.node_id=n.node_id
                   WHERE n.kind NOT IN (
                       'persona', 'relation_policy', 'node_kind_policy', 'tag_policy'
                   )
                   GROUP BY n.node_id
                   ORDER BY degree DESC, n.kind, n.qualified_name
                   LIMIT ?""",
                (max(1, limit),),
            )
        )
        return self._bounded_graph(rows, max(1, limit) * 4)

    def graph_for_nodes(self, node_ids: Sequence[str], limit: int = 64) -> dict[str, Any]:
        """Return a one-hop evidence graph for nodes selected by a context request."""
        seeds = tuple(dict.fromkeys(node_id for node_id in node_ids if node_id))
        if not seeds:
            return {"nodes": [], "edges": []}
        placeholders = ",".join("?" for _ in seeds)
        edges = list(
            self.db.execute(
                f"""SELECT source_id, relation, target_id, evidence_path, confidence
                    FROM edges
                    WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
                    ORDER BY confidence DESC, relation
                    LIMIT ?""",
                (*seeds, *seeds, max(1, limit) * 3),
            )
        )
        ids = set(seeds)
        for edge in edges:
            ids.add(str(edge["source_id"]))
            ids.add(str(edge["target_id"]))
        node_placeholders = ",".join("?" for _ in ids)
        nodes = list(
            self.db.execute(
                f"SELECT *, 0 AS degree FROM nodes WHERE node_id IN ({node_placeholders}) LIMIT ?",
                (*ids, max(1, limit)),
            )
        )
        return self._bounded_graph(nodes, max(1, limit) * 3, edges)

    def _bounded_graph(
        self,
        node_rows: Sequence[sqlite3.Row],
        edge_limit: int,
        edge_rows: Sequence[sqlite3.Row] | None = None,
    ) -> dict[str, Any]:
        node_ids = {str(row["node_id"]) for row in node_rows}
        if edge_rows is None and node_ids:
            placeholders = ",".join("?" for _ in node_ids)
            edge_rows = list(
                self.db.execute(
                    f"""SELECT source_id, relation, target_id, evidence_path, confidence
                        FROM edges
                        WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})
                        ORDER BY confidence DESC, relation LIMIT ?""",
                    (*node_ids, *node_ids, edge_limit),
                )
            )
        bounded_edges = [
            {
                "source": str(row["source_id"]),
                "target": str(row["target_id"]),
                "relation": str(row["relation"]),
                "evidence_path": str(row["evidence_path"]),
                "confidence": round(float(row["confidence"]), 3),
            }
            for row in (edge_rows or ())
            if str(row["source_id"]) in node_ids and str(row["target_id"]) in node_ids
        ][:edge_limit]
        return {
            "nodes": [
                {
                    "id": str(row["node_id"]),
                    "kind": str(row["kind"]),
                    "name": str(row["name"]),
                    "qualified_name": str(row["qualified_name"]),
                    "path": row["path"],
                    "degree": int(row["degree"] or 0),
                }
                for row in node_rows
            ],
            "edges": bounded_edges,
        }

    def metrics_summary(self, repository: str | None = None, limit: int = 20) -> dict[str, Any]:
        where = " WHERE repository=?" if repository else ""
        params: tuple[Any, ...] = (repository,) if repository else ()
        aggregate = self.db.execute(
            "SELECT COUNT(*) count, AVG(duration_ms) avg_ms, "
            "AVG(estimated_tokens) avg_tokens, AVG(result_count) avg_results "
            f"FROM metrics{where}",
            params,
        ).fetchone()
        recent = self.db.execute(
            f"SELECT created_at, operation, repository, duration_ms, estimated_tokens, "
            f"result_count, payload FROM metrics{where} ORDER BY id DESC LIMIT ?",
            (*params, limit),
        )
        return {
            "aggregate": {
                "operations": int(aggregate["count"] or 0),
                "avg_duration_ms": round(float(aggregate["avg_ms"] or 0.0), 2),
                "avg_estimated_tokens": round(float(aggregate["avg_tokens"] or 0.0), 1),
                "avg_result_count": round(float(aggregate["avg_results"] or 0.0), 1),
            },
            "recent": [
                {
                    "created_at": row["created_at"],
                    "operation": row["operation"],
                    "repository": row["repository"],
                    "duration_ms": row["duration_ms"],
                    "estimated_tokens": row["estimated_tokens"],
                    "result_count": row["result_count"],
                    "payload": json.loads(row["payload"] or "{}"),
                }
                for row in recent
            ],
        }

    def export_graph(self) -> tuple[list[GraphNode], list[dict[str, Any]]]:
        return self.all_nodes(), self.all_edges()

    def record_metric(
        self,
        operation: str,
        repository: str,
        duration_ms: float,
        estimated_tokens: int,
        result_count: int,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.db.execute(
            """INSERT INTO metrics(operation, repository, duration_ms,
                                   estimated_tokens, result_count, payload)
               VALUES(?,?,?,?,?,?)""",
            (
                operation,
                repository,
                duration_ms,
                estimated_tokens,
                result_count,
                json.dumps(payload or {}, sort_keys=True),
            ),
        )
        self.db.commit()


def _fts_tokens(text: str) -> Iterable[str]:
    token = []
    for char in text:
        if char.isalnum() or char in {"_", ".", "-"}:
            token.append(char.casefold())
        elif token:
            yield "".join(token).replace('"', "")
            token = []
    if token:
        yield "".join(token).replace('"', "")


def _normalize_search(value: str) -> str:
    return value.casefold().replace("\\", "/").strip()


def _package_name(qualified_name: str, kind: str) -> str:
    owner = qualified_name.split("#", 1)[0]
    if kind == "package":
        return owner.casefold()
    if "." not in owner:
        return ""
    return owner.rsplit(".", 1)[0].casefold()
