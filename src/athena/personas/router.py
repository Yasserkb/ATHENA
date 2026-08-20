from __future__ import annotations

import re

from athena.domain import Persona

_SIGNALS = (
    (
        re.compile(r"\b(review|pull request|merge request|\bpr\b|diff|security review)\b", re.I),
        "reviewer",
    ),
    (re.compile(r"\b(test|tests|coverage|junit|pytest|integration test)\b", re.I), "tester"),
    (
        re.compile(
            r"\b(debug|debugging|fix|bug|error|exception|crash|traceback|stack trace|not working)\b",
            re.I,
        ),
        "debugger",
    ),
    (
        re.compile(
            r"\b(explain|architecture|design|overview|workflow|how does|dependency)\b", re.I
        ),
        "architect",
    ),
    (re.compile(r"\b(document|docs|readme|docstring|adr)\b", re.I), "doc-writer"),
    (re.compile(r"\b(commit|release|changelog|pull request description)\b", re.I), "release"),
    (re.compile(r"\b(implement|add|create|build|feature|refactor|change)\b", re.I), "developer"),
)

_SPECIALIST_PERSONAS = frozenset(
    {
        "backend-developer",
        "cloud-engineer-architect",
        "data-engineer",
        "database-administrator",
        "devops-engineer",
        "frontend-web-developer",
        "fullstack-typescript-developer",
        "mern-developer",
        "mobile-developer",
        "python-developer",
        "qa-test-automation-engineer",
        "security-analyst",
        "spring-angular-developer",
        "t3-developer",
        "t4-universal-developer",
    }
)

_INTENT_PERSONAS = frozenset({"debugger", "doc-writer", "release", "reviewer", "tester"})


class PersonaRouter:
    def route(self, text: str, personas: dict[str, Persona]) -> tuple[Persona, float]:
        lowered = text.casefold()
        scores = {persona_id: 0.0 for persona_id in personas}
        for persona_id, persona in personas.items():
            for trigger in persona.triggers:
                pattern = r"(?<!\w)" + re.escape(trigger.casefold()) + r"(?!\w)"
                if re.search(pattern, lowered):
                    scores[persona_id] += 1.0
        matched_specialists = {
            persona_id for persona_id in _SPECIALIST_PERSONAS if scores.get(persona_id, 0.0) > 0
        }
        for persona_id in matched_specialists:
            scores[persona_id] += 1.25
        for regex, persona_id in _SIGNALS:
            if persona_id in scores and regex.search(text):
                scores[persona_id] += 0.8
                # Explicit delivery intent (for example, "document this database migration")
                # should not be displaced by incidental technical-domain vocabulary.
                if persona_id in _INTENT_PERSONAS:
                    scores[persona_id] += 1.5
        test_creation = re.search(
            r"\b(?:add|write|create|implement)\s+(?:unit\s+|integration\s+)?tests?\b",
            lowered,
        )
        implementation = re.search(r"\b(?:implement|add|create|build|refactor|change)\b", lowered)
        if (
            implementation
            and not test_creation
            and not matched_specialists
            and "developer" in scores
        ):
            scores["developer"] += 0.65
        best_id = max(scores, key=lambda key: scores[key]) if scores else "developer"
        top = scores.get(best_id, 0.0)
        if top <= 0:
            return personas["developer"], 0.0
        ordered = sorted(scores.values(), reverse=True)
        second = ordered[1] if len(ordered) > 1 else 0.0
        confidence = min(1.0, 0.55 + (top - second) / max(1.0, top + second))
        return personas[best_id], round(confidence, 3)
