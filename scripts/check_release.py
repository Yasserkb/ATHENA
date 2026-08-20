from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PUBLIC_FILES = (
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "VALIDATION.md",
)
LOCAL_PARTS = frozenset({".agents", ".athena", ".claude", ".codex", ".cursor", ".idea", ".vscode"})
LOCAL_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key")


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    missing = [name for name in REQUIRED_PUBLIC_FILES if not (ROOT / name).is_file()]
    if missing:
        fail(f"Missing public release files: {', '.join(missing)}")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = str(project["version"])
    expected_fragments = {
        "src/athena/__init__.py": f'return "{version}"',
        "Dockerfile": f"ARG VERSION={version}",
        "compose.yaml": f"ATHENA_VERSION:-{version}",
        ".env.docker.example": f"ATHENA_VERSION={version}",
        "CHANGELOG.md": f"## [{version}]",
        "VALIDATION.md": f"Athena `{version}`",
    }
    for relative, fragment in expected_fragments.items():
        if fragment not in (ROOT / relative).read_text(encoding="utf-8"):
            fail(f"Release version {version} is not synchronized in {relative}")

    tracked = (
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .split("\0")
    )
    local = [
        path
        for path in tracked
        if path
        and (
            any(part in LOCAL_PARTS for part in Path(path).parts)
            or path.casefold().endswith(LOCAL_SUFFIXES)
        )
    ]
    if local:
        fail(f"Local/private artifacts are tracked: {', '.join(local)}")

    mutable_actions: list[str] = []
    action_pattern = re.compile(r"\buses:\s+[^\s@]+@([^\s#]+)")
    for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
        for reference in action_pattern.findall(workflow.read_text(encoding="utf-8")):
            if not re.fullmatch(r"[0-9a-f]{40}", reference):
                mutable_actions.append(f"{workflow.name}@{reference}")
    if mutable_actions:
        fail(f"GitHub Actions are not pinned to commits: {', '.join(mutable_actions)}")

    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "Dockerfile", ROOT / "compose.yaml", ROOT / "README.md")
    )
    if "OWNER/athena-codegraph" in public_text:
        fail("Public documentation or image metadata still contains the OWNER placeholder")

    print(f"Validated public release metadata for Athena {version}")


if __name__ == "__main__":
    main()
