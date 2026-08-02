from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecretMatch:
    kind: str
    start: int
    end: int


class SecretDetector:
    _patterns = (
        ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
        (
            "generic_secret",
            re.compile(
                r'(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*["\']?[^\s"\']{8,}'
            ),
        ),
    )

    def find(self, text: str) -> list[SecretMatch]:
        matches: list[SecretMatch] = []
        for kind, pattern in self._patterns:
            matches.extend(SecretMatch(kind, m.start(), m.end()) for m in pattern.finditer(text))
        return sorted(matches, key=lambda x: x.start)

    def contains_secret(self, text: str) -> bool:
        return bool(self.find(text))

    def redact(self, text: str) -> str:
        matches = self.find(text)
        if not matches:
            return text
        pieces: list[str] = []
        cursor = 0
        for match in matches:
            if match.start < cursor:
                continue
            pieces.append(text[cursor : match.start])
            pieces.append(f"<REDACTED:{match.kind}>")
            cursor = match.end
        pieces.append(text[cursor:])
        return "".join(pieces)
