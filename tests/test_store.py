import sqlite3
from pathlib import Path

import pytest

from athena.domain import Chunk, Edge, Evidence, FileRecord, GraphNode, IndexedFileAnalysis
from athena.storage import SQLiteStore


def test_fts_and_exact_search(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db")
    try:
        node = GraphNode(
            "java::A", "class", "PaymentService", "com.acme.PaymentService", "A.java", 1, 10
        )
        chunk = Chunk(
            "c1",
            "A.java",
            1,
            10,
            "class PaymentService { void authorize() {} }",
            "h",
            node.node_id,
            "java",
            ("service",),
        )
        record = FileRecord("A.java", tmp_path / "A.java", "hash", 10, 1, "java")
        store.replace_file_analysis(record, (node,), (), (chunk,))
        assert store.exact_nodes(["PaymentService"])[0][0].node_id == node.node_id
        assert store.exact_nodes(["Payment"])[0][0].node_id == node.node_id
        results = store.lexical_chunks("authorize payment", 10)
        assert results and results[0][0].chunk_id == "c1"
    finally:
        store.close()


def _analysis(tmp_path: Path, name: str) -> IndexedFileAnalysis:
    path = f"{name}.py"
    node = GraphNode(f"python::{name}", "class", name, name, path, 1, 2)
    chunk = Chunk(
        f"chunk::{name}",
        path,
        1,
        2,
        f"class {name}:\n    pass",
        f"hash::{name}",
        node.node_id,
        "python",
    )
    record = FileRecord(path, tmp_path / path, f"hash::{name}", 20, 1, "python")
    return IndexedFileAnalysis(record, (node,), (), (chunk,))


def test_batch_replacement_uses_one_transaction(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db")
    statements: list[str] = []
    store.db.set_trace_callback(statements.append)
    try:
        store.replace_file_analyses((_analysis(tmp_path, "One"), _analysis(tmp_path, "Two")))
        assert sum(statement == "BEGIN IMMEDIATE" for statement in statements) == 1
        assert store.stats()["files"] == 2
    finally:
        store.close()


def test_batch_replacement_rolls_back_completely(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db")
    original = _analysis(tmp_path, "Original")
    store.replace_file_analyses((original,))
    generation = store.index_generation()
    invalid = _analysis(tmp_path, "Invalid")
    missing_edge = Edge(
        invalid.nodes[0].node_id,
        "DEPENDS_ON",
        "missing-node",
        Evidence(invalid.file.path, 1, 1, "hash", "test"),
    )
    invalid = IndexedFileAnalysis(invalid.file, invalid.nodes, (missing_edge,), invalid.chunks)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            store.replace_file_analyses((_analysis(tmp_path, "Replacement"), invalid))
        assert store.indexed_paths() == {"Original.py"}
        assert store.index_generation() == generation
    finally:
        store.close()


def test_v1_database_is_migrated_and_search_index_is_rebuilt(tmp_path: Path) -> None:
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO metadata(key, value) VALUES('schema_version', '1');
        CREATE TABLE nodes (
            node_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            path TEXT,
            start_line INTEGER NOT NULL DEFAULT 0,
            end_line INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '{}'
        );
        INSERT INTO nodes(node_id, kind, name, qualified_name, path)
        VALUES('java::Legacy', 'class', 'LegacyService', 'com.acme.LegacyService',
               'src/LegacyService.java');
        """
    )
    connection.commit()
    connection.close()

    store = SQLiteStore(database)
    try:
        columns = {row["name"] for row in store.db.execute("PRAGMA table_info(nodes)")}
        assert {
            "name_normalized",
            "simple_name",
            "qualified_name_normalized",
            "path_normalized",
            "package_name",
        } <= columns
        assert store.metadata()["schema_version"] == "2"
        assert store.exact_nodes(["LegacyService"])[0][0].node_id == "java::Legacy"
        assert store.db.execute("SELECT COUNT(*) FROM nodes_fts").fetchone()[0] == 1
    finally:
        store.close()


def test_normalized_exact_lookup_uses_index(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db")
    try:
        store.replace_file_analyses((_analysis(tmp_path, "IndexedService"),))
        plan = store.db.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM nodes WHERE name_normalized=?",
            ("indexedservice",),
        )
        assert any("idx_nodes_name_normalized" in row["detail"] for row in plan)
    finally:
        store.close()


def test_graph_walk_batches_edge_and_node_queries_per_depth(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db")
    root = GraphNode("node::root", "class", "Root", "pkg.Root")
    children = tuple(
        GraphNode(f"node::child{index}", "class", f"Child{index}", f"pkg.Child{index}")
        for index in range(5)
    )
    leaves = tuple(
        GraphNode(f"node::leaf{index}", "class", f"Leaf{index}", f"pkg.Leaf{index}")
        for index in range(5)
    )
    nodes = (root, *children, *leaves)
    first_hop = tuple(
        Edge(
            root.node_id,
            "DEPENDS_ON",
            children[index].node_id,
            Evidence("@test", index + 1, index + 1, "hash", "test"),
        )
        for index in range(5)
    )
    second_hop = tuple(
        Edge(
            children[index].node_id,
            "DEPENDS_ON",
            leaves[index].node_id,
            Evidence("@test", index + 10, index + 10, "hash", "test"),
        )
        for index in range(5)
    )
    try:
        store.upsert_global_nodes(nodes)
        store.upsert_global_edges((*first_hop, *second_hop))
        statements: list[str] = []
        store.db.set_trace_callback(statements.append)

        walked = store.graph_walk((root.node_id,), ("DEPENDS_ON",), depth=2, max_nodes=20)

        assert {node.node_id for node, _, _ in walked} == {
            *(node.node_id for node in children),
            *(node.node_id for node in leaves),
        }
        assert [distance for _, distance, _ in walked].count(1) == 5
        assert [distance for _, distance, _ in walked].count(2) == 5
        edge_queries = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith("SELECT") and "FROM edges" in statement
        ]
        node_queries = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith("SELECT")
            and "FROM nodes WHERE node_id IN" in statement
        ]
        assert len(edge_queries) == 2
        assert len(node_queries) == 2

        plan = store.db.execute(
            """EXPLAIN QUERY PLAN
               SELECT relation, source_id, target_id FROM edges
               WHERE source_id IN (?, ?) OR target_id IN (?, ?)""",
            ("node::root", "node::child0", "node::root", "node::child0"),
        )
        details = " ".join(str(row["detail"]) for row in plan)
        assert "MULTI-INDEX OR" in details
        assert "source_id=?" in details
        assert "idx_edges_target" in details
    finally:
        store.close()


def test_generation_aware_query_caches_invalidate_after_mutation(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "index.db", cache_max_entries=2)
    try:
        store.replace_file_analyses((_analysis(tmp_path, "CachedService"),))
        generation = store.index_generation()

        assert store.exact_nodes(["CachedService"])
        assert store.exact_nodes(["CachedService"])
        assert store.lexical_chunks("CachedService")
        assert store.lexical_chunks("CachedService")
        assert store.graph_walk(("python::CachedService",), (), 2, 20) == []
        assert store.graph_walk(("python::CachedService",), (), 2, 20) == []
        warm = store.cache_status()
        assert warm["exact_nodes"]["hits"] == 1
        assert warm["lexical_chunks"]["hits"] == 1
        assert warm["graph_walk"]["hits"] == 1

        store.delete_file("CachedService.py")

        assert store.index_generation() == generation + 1
        assert not store.exact_nodes(["CachedService"])
        status = store.cache_status()
        assert status["exact_nodes"]["invalidations"] == 1
        assert status["lexical_chunks"]["invalidations"] == 1
        assert status["graph_walk"]["invalidations"] == 1

        store.exact_nodes(["One"])
        store.exact_nodes(["Two"])
        store.exact_nodes(["Three"])
        bounded = store.cache_status()["exact_nodes"]
        assert bounded["entries"] == 2
        assert bounded["evictions"] >= 1
    finally:
        store.close()


def test_generation_change_from_second_connection_invalidates_cache(tmp_path: Path) -> None:
    database = tmp_path / "index.db"
    first = SQLiteStore(database)
    second = SQLiteStore(database)
    try:
        first.replace_file_analyses((_analysis(tmp_path, "CrossProcess"),))
        assert first.exact_nodes(["CrossProcess"])
        assert first.exact_nodes(["CrossProcess"])

        second.delete_file("CrossProcess.py")

        assert not first.exact_nodes(["CrossProcess"])
        assert first.cache_status()["exact_nodes"]["invalidations"] == 1
    finally:
        second.close()
        first.close()
