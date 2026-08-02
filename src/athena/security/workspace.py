from __future__ import annotations

from pathlib import Path

from athena.errors import WorkspaceViolation


class WorkspaceGuard:
    def __init__(self, root: Path, restrict: bool = True) -> None:
        self.root = root.expanduser().resolve()
        self.restrict = restrict
        if not self.root.is_dir():
            raise WorkspaceViolation(f"Workspace does not exist or is not a directory: {self.root}")

    def resolve(self, path: Path | str = ".") -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        if self.restrict and candidate != self.root and self.root not in candidate.parents:
            raise WorkspaceViolation(f"Path escapes workspace {self.root}: {candidate}")
        return candidate

    def relative(self, path: Path) -> str:
        return self.resolve(path).relative_to(self.root).as_posix()
