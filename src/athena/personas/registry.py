from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from athena.domain import Persona, PersonaRetrievalPolicy
from athena.errors import ConfigurationError


class _PolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_kinds: list[str] = Field(default_factory=list)
    traverse_relations: list[str] = Field(default_factory=list)
    include_tags: list[str] = Field(default_factory=list)
    max_context_tokens: int = Field(default=2400, ge=300, le=20_000)
    max_chunks_per_file: int = Field(default=3, ge=1, le=20)
    graph_depth: int = Field(default=2, ge=0, le=5)


class _PersonaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    purpose: str
    triggers: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    output: str
    retrieval: _PolicyModel = Field(default_factory=_PolicyModel)

    def to_domain(self) -> Persona:
        policy = self.retrieval
        return Persona(
            self.id,
            self.purpose,
            tuple(self.triggers),
            tuple(self.rules),
            self.output,
            PersonaRetrievalPolicy(
                tuple(policy.start_kinds),
                tuple(policy.traverse_relations),
                tuple(policy.include_tags),
                policy.max_context_tokens,
                policy.max_chunks_per_file,
                policy.graph_depth,
            ),
        )


class PersonaRegistry:
    def __init__(self, root: Path, extra_dirs: list[str] | None = None) -> None:
        self.root = root
        self.extra_dirs = extra_dirs or []
        self._personas = self._load()

    def _load(self) -> dict[str, Persona]:
        loaded: dict[str, Persona] = {}
        builtin = files("athena.personas.definitions")
        for item in builtin.iterdir():
            if item.name.endswith((".yaml", ".yml")):
                persona = self._parse(item.read_text(encoding="utf-8"), item.name)
                loaded[persona.persona_id] = persona
        for value in self.extra_dirs:
            directory = Path(value)
            if not directory.is_absolute():
                directory = self.root / directory
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.y*ml")):
                persona = self._parse(path.read_text(encoding="utf-8"), str(path))
                loaded[persona.persona_id] = persona
        if "developer" not in loaded:
            raise ConfigurationError("The effective persona registry must contain 'developer'")
        return loaded

    @staticmethod
    def _parse(raw: str, source: str) -> Persona:
        try:
            data: Any = yaml.safe_load(raw) or {}
            return _PersonaModel.model_validate(data).to_domain()
        except (yaml.YAMLError, ValidationError) as exc:
            raise ConfigurationError(f"Invalid persona {source}: {exc}") from exc

    def all(self) -> dict[str, Persona]:
        return dict(self._personas)

    def get(self, persona_id: str) -> Persona:
        try:
            return self._personas[persona_id]
        except KeyError as exc:
            raise ConfigurationError(f"Unknown persona: {persona_id}") from exc
