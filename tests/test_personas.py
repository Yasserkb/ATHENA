from pathlib import Path

from athena.orchestrator import AthenaRuntime
from athena.personas import (
    PersonaRegistry,
    PersonaRouter,
    install_persona_knowledge,
    install_senior_developer_knowledge,
    packaged_knowledge_files,
)
from athena.retrieval import apply_profile, resolve_profile


def test_personas_have_retrieval_policies(tmp_path: Path) -> None:
    registry = PersonaRegistry(tmp_path)
    personas = registry.all()
    assert "developer" in personas
    assert personas["developer"].policy.max_context_tokens >= 1000
    routed, confidence = PersonaRouter().route("fix this failing junit test", personas)
    assert routed.persona_id in {"debugger", "tester"}
    assert confidence > 0


def test_explicit_debug_intent_beats_incidental_stack_and_backend_terms(tmp_path: Path) -> None:
    personas = PersonaRegistry(tmp_path).all()

    routed, confidence = PersonaRouter().route(
        "Debug the FastAPI UserService get_user endpoint and test_get_user",
        personas,
    )

    assert routed.persona_id == "debugger"
    assert confidence > 0


def test_senior_developer_is_manually_selectable(tmp_path: Path) -> None:
    personas = PersonaRegistry(tmp_path).all()
    assert personas["senior-developer"].policy.max_context_tokens == 4600

    automatic, _ = PersonaRouter().route(
        "Design a production-safe cross-cutting database migration with rollback",
        personas,
    )
    ordinary, _ = PersonaRouter().route("Implement a focused validation change", personas)
    documentation, _ = PersonaRouter().route(
        "Document the database migration in the README",
        personas,
    )

    assert automatic.persona_id != "senior-developer"
    assert ordinary.persona_id == "developer"
    assert documentation.persona_id == "doc-writer"


def test_senior_knowledge_install_preserves_local_customizations(tmp_path: Path) -> None:
    written = install_senior_developer_knowledge(tmp_path)
    knowledge = tmp_path / ".athena" / "knowledge" / "senior-developer"
    assert {path.name for path in written} == {
        "SENIOR_DEVELOPER_PERSONA.md",
        "SYSTEM_DESIGN_PLAYBOOK.md",
        "DESIGN_PATTERNS_PLAYBOOK.md",
    }
    assert "requirements" in (knowledge / "SYSTEM_DESIGN_PLAYBOOK.md").read_text(encoding="utf-8")

    customized = knowledge / "SENIOR_DEVELOPER_PERSONA.md"
    customized.write_text("local customization", encoding="utf-8")
    assert install_senior_developer_knowledge(tmp_path) == []
    assert customized.read_text(encoding="utf-8") == "local customization"

    overwritten = install_senior_developer_knowledge(tmp_path, overwrite=True)
    assert len(overwritten) == 3
    assert customized.read_text(encoding="utf-8").startswith("# Athena Persona")

    system_playbook = knowledge / "SYSTEM_DESIGN_PLAYBOOK.md"
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        indexed = runtime.store.indexed_paths()
        system_playbook.write_text(
            system_playbook.read_text(encoding="utf-8") + "\nLocal rule.\n",
            encoding="utf-8",
        )
        refresh = runtime.scan()
    assert ".athena/knowledge/senior-developer/SYSTEM_DESIGN_PLAYBOOK.md" in indexed
    assert refresh.scanned == 1


def test_all_packaged_knowledge_is_installed_without_operational_snippets(tmp_path: Path) -> None:
    expected = packaged_knowledge_files()
    written = install_persona_knowledge(tmp_path)

    assert set(expected) >= {"developer", "senior-developer", "security-analyst", "devops-engineer"}
    assert len(written) == sum(len(names) for names in expected.values())
    for persona_id, names in expected.items():
        destination = tmp_path / ".athena" / "knowledge" / persona_id
        assert {path.name for path in destination.glob("*.md")} == set(names)
        assert not any("COPILOT_INSTRUCTIONS_SNIPPET" in name for name in names)

    customized = written[0]
    customized.write_text("local customization", encoding="utf-8")
    assert install_persona_knowledge(tmp_path) == []
    assert customized.read_text(encoding="utf-8") == "local customization"


def test_specialist_personas_beat_generic_implementation_wording(tmp_path: Path) -> None:
    personas = PersonaRegistry(tmp_path).all()
    examples = {
        "Implement a Kubernetes deployment with Terraform": "devops-engineer",
        "Implement a Python FastAPI endpoint": "python-developer",
        "Implement a PostgreSQL migration and tune its index": "database-administrator",
        "Implement a threat model for API secrets": "security-analyst",
        "Implement a Kafka data pipeline": "data-engineer",
    }
    for task, expected in examples.items():
        routed, confidence = PersonaRouter().route(task, personas)
        assert routed.persona_id == expected
        assert confidence > 0


def test_persona_cards_reserve_budget_for_repository_evidence(tmp_path: Path) -> None:
    developer = PersonaRegistry(tmp_path).get("developer")
    card = developer.prompt_card()

    assert "Classify the task" in card
    assert "Apply the persona's indexed playbooks" in card
    assert "Finish with affected files" not in card


def test_retrieval_profiles_have_predictable_budgets(tmp_path: Path) -> None:
    persona = PersonaRegistry(tmp_path).get("developer")
    assert resolve_profile("Explain cross-module workflow", None) == "deep"
    assert resolve_profile("Fix PaymentClient", None) == "eco"
    assert apply_profile(persona, "eco").policy.graph_depth == 1
    assert apply_profile(persona, "deep").policy.max_context_tokens >= 6000
    copilot = apply_profile(persona, "copilot-economy")
    assert copilot.policy.max_context_tokens == 1200
    assert copilot.policy.max_chunks_per_file == 1
    assert copilot.policy.graph_depth == 1
