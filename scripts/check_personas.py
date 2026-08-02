from pathlib import Path

from athena.personas import PersonaRegistry, packaged_knowledge_files


def main() -> None:
    root = Path.cwd()
    personas = PersonaRegistry(root).all()
    required = {"developer", "debugger", "architect", "reviewer", "tester", "senior-developer"}
    missing = required - personas.keys()
    if missing:
        raise SystemExit(f"Missing personas: {sorted(missing)}")
    for persona in personas.values():
        if not persona.policy.traverse_relations:
            raise SystemExit(f"Persona has no graph traversal policy: {persona.persona_id}")
    unknown_knowledge = set(packaged_knowledge_files()) - personas.keys()
    if unknown_knowledge:
        raise SystemExit(f"Knowledge exists without a persona: {sorted(unknown_knowledge)}")
    print(f"Validated {len(personas)} personas")


if __name__ == "__main__":
    main()
