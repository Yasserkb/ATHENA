from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

from athena import __version__
from athena.config import database_path, load_config, state_directory
from athena.daemon import load_daemon_status


def main() -> int:
    root = Path(os.getenv("ATHENA_ROOT", "/workspace")).resolve()
    if not root.is_dir():
        raise RuntimeError(f"workspace is unavailable: {root}")

    state = state_directory()
    if state is None:
        raise RuntimeError("ATHENA_STATE_DIR is required in the production container")
    state.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".health-", dir=state):
        pass

    database = database_path(root, load_config(root))
    database_status = "not-created"
    if database.exists():
        connection = sqlite3.connect(database, timeout=3)
        try:
            connection.execute("PRAGMA query_only=ON")
            row = connection.execute("PRAGMA quick_check(1)").fetchone()
            if row is None or row[0] != "ok":
                raise RuntimeError(f"SQLite quick_check failed: {row}")
            database_status = "ok"
        finally:
            connection.close()

    daemon = load_daemon_status(root)
    if not daemon.get("process_alive") or not daemon.get("process_matches_daemon"):
        raise RuntimeError("Athena daemon process is not active")
    if daemon.get("state") not in {"scanning", "idle", "pending"}:
        raise RuntimeError(f"Athena daemon state is {daemon.get('state', 'missing')}")

    print(
        json.dumps(
            {
                "status": "ok",
                "version": __version__,
                "workspace": str(root),
                "state": str(state),
                "database": database_status,
                "daemon": daemon.get("state"),
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"unhealthy: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
