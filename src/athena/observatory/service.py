from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena.daemon import load_daemon_status
from athena.indexing.scanner import git_head
from athena.storage import SQLiteStore

from .registry import ProjectEntry, ProjectRegistry


class ObservatoryService:
    """Read-only aggregation service over registered Athena repository indexes."""

    def __init__(self, registry: ProjectRegistry) -> None:
        self.registry = registry

    def overview(self) -> dict[str, Any]:
        projects = [self._project(entry, include_graph=False) for entry in self.registry.all()]
        savings = [project.get("savings", {}) for project in projects]
        total_baseline = sum(int(item.get("baseline_tokens", 0)) for item in savings)
        total_delivered = sum(int(item.get("tokens_delivered", 0)) for item in savings)
        total_avoided = max(0, total_baseline - total_delivered)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "projects": projects,
            "summary": {
                "projects": len(projects),
                "healthy_projects": sum(project.get("health") == "healthy" for project in projects),
                "context_requests": sum(int(item.get("context_requests", 0)) for item in savings),
                "baseline_tokens": total_baseline,
                "tokens_delivered": total_delivered,
                "tokens_avoided": total_avoided,
                "savings_rate": (
                    round(total_avoided / total_baseline, 4) if total_baseline else 0.0
                ),
                "nodes": sum(int(project.get("stats", {}).get("nodes", 0)) for project in projects),
                "edges": sum(int(project.get("stats", {}).get("edges", 0)) for project in projects),
            },
            "methodology": {
                "label": "Estimated context tokens avoided",
                "baseline": "The indexed repository's UTF-8 byte size divided by 3.6, once per context request.",
                "actual": "The measured or estimated tokens in Athena's serialized context result.",
                "caveat": "This is a counterfactual context-efficiency estimate, not a provider invoice or guaranteed billing reduction.",
            },
        }

    def project(self, project_id: str) -> dict[str, Any]:
        entry = self.registry.get(project_id)
        if entry is None:
            raise KeyError(project_id)
        return self._project(entry, include_graph=True)

    def register(self, root: Path, database: Path | None = None) -> dict[str, Any]:
        return self._project(self.registry.add(root, database), include_graph=False)

    def remove(self, project_id: str) -> bool:
        return self.registry.remove(project_id)

    def _project(self, entry: ProjectEntry, *, include_graph: bool) -> dict[str, Any]:
        base: dict[str, Any] = {
            "id": entry.project_id,
            "name": entry.root.name,
            "root": str(entry.root),
            "database": str(entry.database),
            "added_at": entry.added_at,
            "initialized": entry.database.is_file(),
        }
        if not entry.root.is_dir():
            return {
                **base,
                "health": "missing",
                "health_score": 0,
                "message": "Repository directory is no longer available.",
                "stats": {},
                "savings": {},
            }
        if not entry.database.is_file():
            return {
                **base,
                "health": "uninitialized",
                "health_score": 15,
                "message": "Run athena scan to create the index.",
                "stats": {},
                "savings": {},
            }
        try:
            with SQLiteStore(entry.database) as store:
                metadata = store.metadata()
                stats = store.stats()
                repository = metadata.get("repository_name", entry.root.name)
                metrics = store.observatory_metrics(repository, 40)
                current_commit = git_head(entry.root)
                indexed_commit = metadata.get("indexed_commit")
                stale = bool(
                    current_commit and indexed_commit not in {current_commit, "working-tree"}
                )
                daemon = self._daemon(entry)
                degraded = metadata.get("index_degraded") == "true"
                health, score, message = _health(degraded, stale, daemon, stats)
                kinds = {
                    str(row["kind"]): int(row["count"])
                    for row in store.db.execute(
                        "SELECT kind, COUNT(*) count FROM nodes GROUP BY kind ORDER BY count DESC"
                    )
                }
                result = {
                    **base,
                    "name": repository,
                    "health": health,
                    "health_score": score,
                    "message": message,
                    "repository_id": metadata.get("repository_id"),
                    "indexed_commit": indexed_commit,
                    "current_commit": current_commit,
                    "stale": stale,
                    "degraded": degraded,
                    "last_scan_epoch": metadata.get("last_scan_epoch"),
                    "index_generation": store.index_generation(),
                    "stats": stats,
                    "node_kinds": kinds,
                    "daemon": daemon,
                    "savings": metrics["savings"],
                    "contexts": metrics["contexts"],
                    "activity": metrics["recent"],
                }
                if include_graph:
                    result["graph"] = store.graph_overview(54)
                    latest = next(
                        (
                            context
                            for context in metrics["contexts"]
                            if context.get("selected_evidence")
                        ),
                        None,
                    )
                    symbol_ids = [
                        str(item["symbol_id"])
                        for item in (latest or {}).get("selected_evidence", [])
                        if item.get("symbol_id")
                    ]
                    result["retrieval_graph"] = store.graph_for_nodes(symbol_ids, 54)
                    result["latest_context"] = latest
                return result
        except Exception as exc:
            return {
                **base,
                "health": "error",
                "health_score": 0,
                "message": f"Index could not be read: {exc}",
                "stats": {},
                "savings": {},
            }

    @staticmethod
    def _daemon(entry: ProjectEntry) -> dict[str, Any]:
        local_database = (entry.root / ".athena" / "index.db").resolve()
        if entry.database == local_database:
            return load_daemon_status(entry.root)
        status_path = entry.database.parent / "daemon" / "status.json"
        if not status_path.is_file():
            return {"state": "not-running", "process_alive": False, "heartbeat_age_seconds": None}
        try:
            payload: dict[str, Any] = json.loads(status_path.read_text(encoding="utf-8"))
            heartbeat = datetime.fromisoformat(str(payload.get("heartbeat_at"))).timestamp()
            payload["heartbeat_age_seconds"] = round(max(0.0, time.time() - heartbeat), 3)
            payload.setdefault("process_alive", payload.get("state") not in {"stopped", "error"})
            return payload
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {"state": "unknown", "process_alive": False, "heartbeat_age_seconds": None}


def _health(
    degraded: bool,
    stale: bool,
    daemon: dict[str, Any],
    stats: dict[str, int],
) -> tuple[str, int, str]:
    score = 100
    reasons: list[str] = []
    if not stats.get("files"):
        score -= 40
        reasons.append("index is empty")
    if degraded:
        score -= 45
        reasons.append("index is degraded")
    if stale:
        score -= 25
        reasons.append("Git commit is newer than the index")
    daemon_state = str(daemon.get("state", "not-running"))
    heartbeat_age = daemon.get("heartbeat_age_seconds")
    daemon_fresh = bool(
        daemon.get("process_alive")
        and daemon_state not in {"stopped", "error"}
        and (heartbeat_age is None or float(heartbeat_age) <= 30.0)
    )
    if not daemon_fresh:
        score -= 20
        reasons.append("daemon is not fresh")
    score = max(0, score)
    if degraded or score < 45:
        state = "critical"
    elif stale or not daemon_fresh:
        state = "attention"
    else:
        state = "healthy"
    message = "; ".join(reasons).capitalize() if reasons else "Index and daemon are healthy."
    return state, score, message
