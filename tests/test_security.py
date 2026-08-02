from pathlib import Path

import pytest

from athena.errors import WorkspaceViolation
from athena.security import SecretDetector, WorkspaceGuard


def test_workspace_guard_blocks_escape(tmp_path: Path) -> None:
    guard = WorkspaceGuard(tmp_path)
    with pytest.raises(WorkspaceViolation):
        guard.resolve(tmp_path.parent)


def test_secret_detector_redacts_value() -> None:
    detector = SecretDetector()
    value = 'api_key="abcdefghijklmnopqrstuvwxyz123456"'
    redacted = detector.redact(value)
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "<REDACTED:generic_secret>" in redacted
