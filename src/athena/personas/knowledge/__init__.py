"""Packaged, selectively indexed persona knowledge."""

from __future__ import annotations

from collections.abc import Iterable
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

_SENIOR_DEVELOPER_FILES = (
    "SENIOR_DEVELOPER_PERSONA.md",
    "SYSTEM_DESIGN_PLAYBOOK.md",
    "DESIGN_PATTERNS_PLAYBOOK.md",
)


def packaged_knowledge_files(persona_id: str | None = None) -> dict[str, tuple[str, ...]]:
    """Return installable knowledge files grouped by persona.

    Knowledge is copied into a target repository's ``.athena`` directory because that is
    the packaged guidance the scanner indexes. Operational instruction snippets are excluded:
    they configure a host, but are not useful retrieval evidence.
    """
    source = files("athena.personas.knowledge")
    grouped: dict[str, tuple[str, ...]] = {}
    for directory in source.iterdir():
        if not directory.is_dir() or directory.name == "__pycache__":
            continue
        names = tuple(
            item.name
            for item in sorted(directory.iterdir(), key=lambda item: item.name)
            if item.name.endswith(".md")
            and not item.name.startswith("COPILOT_INSTRUCTIONS_SNIPPET")
        )
        if names:
            grouped[directory.name] = names

    # The upgraded suite keeps these established playbooks in developer/. Keep the
    # senior-developer destination stable and prevent duplicate generic retrieval.
    developer = list(grouped.get("developer", ()))
    senior_files = [name for name in _SENIOR_DEVELOPER_FILES if name in developer]
    if senior_files:
        grouped["developer"] = tuple(name for name in developer if name not in senior_files)
        grouped["senior-developer"] = tuple(senior_files)

    if persona_id is None:
        return dict(sorted(grouped.items()))
    return {persona_id: grouped[persona_id]} if persona_id in grouped else {}


def _source_directory(persona_id: str) -> Traversable:
    source = files("athena.personas.knowledge")
    return source.joinpath("developer" if persona_id == "senior-developer" else persona_id)


def install_persona_knowledge(
    root: Path, overwrite: bool = False, persona_ids: Iterable[str] | None = None
) -> list[Path]:
    """Install selected packaged knowledge without overwriting local customizations."""
    selected = set(persona_ids) if persona_ids is not None else None
    written: list[Path] = []
    for persona_id, names in packaged_knowledge_files().items():
        if selected is not None and persona_id not in selected:
            continue
        destination = root / ".athena" / "knowledge" / persona_id
        destination.mkdir(parents=True, exist_ok=True)
        source = _source_directory(persona_id)
        for name in names:
            target = destination / name
            if target.exists() and not overwrite:
                continue
            target.write_text(source.joinpath(name).read_text(encoding="utf-8"), encoding="utf-8")
            written.append(target)
    return written


def install_senior_developer_knowledge(root: Path, overwrite: bool = False) -> list[Path]:
    """Compatibility wrapper for the original selective installer."""
    return install_persona_knowledge(root, overwrite, ("senior-developer",))
