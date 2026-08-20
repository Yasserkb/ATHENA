from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena.config import database_path, load_config
from athena.errors import AthenaError
from athena.indexing.common import stable_id


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    project_id: str
    root: Path
    database: Path
    added_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.project_id,
            "root": str(self.root),
            "database": str(self.database),
            "added_at": self.added_at,
        }


def default_registry_path() -> Path:
    configured = os.getenv("ATHENA_OBSERVATORY_STATE", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".athena" / "observatory.json").resolve()


class ProjectRegistry:
    """Small local registry of repositories visible to Athena Observatory."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or default_registry_path()).expanduser().resolve()

    def all(self) -> tuple[ProjectEntry, ...]:
        data = self._read()
        entries: list[ProjectEntry] = []
        for item in data.get("projects", []):
            try:
                root = Path(str(item["root"])).expanduser().resolve()
                database = Path(str(item["database"])).expanduser().resolve()
                entries.append(
                    ProjectEntry(
                        str(item["id"]),
                        root,
                        database,
                        str(item.get("added_at", "")),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return tuple(
            sorted(entries, key=lambda entry: (entry.root.name.casefold(), str(entry.root)))
        )

    def get(self, project_id: str) -> ProjectEntry | None:
        return next((entry for entry in self.all() if entry.project_id == project_id), None)

    def add(self, root: Path, database: Path | None = None) -> ProjectEntry:
        resolved = root.expanduser().resolve()
        if not resolved.is_dir():
            raise AthenaError(f"Repository root does not exist or is not a directory: {resolved}")
        selected_database = (
            database.expanduser().resolve()
            if database is not None
            else database_path(resolved, load_config(resolved))
        )
        project_id = stable_id("project", str(resolved).casefold())
        existing = {entry.project_id: entry for entry in self.all()}
        entry = ProjectEntry(
            project_id,
            resolved,
            selected_database,
            existing.get(
                project_id,
                ProjectEntry(
                    project_id, resolved, selected_database, datetime.now(UTC).isoformat()
                ),
            ).added_at,
        )
        existing[project_id] = entry
        self._write(tuple(existing.values()))
        return entry

    def remove(self, project_id: str) -> bool:
        entries = self.all()
        remaining = tuple(entry for entry in entries if entry.project_id != project_id)
        if len(remaining) == len(entries):
            return False
        self._write(remaining)
        return True

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema_version": 1, "projects": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AthenaError(f"Invalid Observatory registry {self.path}: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise AthenaError(f"Unsupported Observatory registry schema: {self.path}")
        return data

    def _write(self, entries: tuple[ProjectEntry, ...]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "projects": [entry.to_dict() for entry in entries],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
