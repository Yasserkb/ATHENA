from __future__ import annotations

import re
from urllib.parse import urlsplit

_PARAMETER = re.compile(r"(?:\{[^}/]+\}|:[A-Za-z_]\w*|\$\{[^}]+\}|<[^>/]+>|\[[A-Za-z_]\w*\])")
_MULTISLASH = re.compile(r"/+")


def canonical_route(raw: str) -> str:
    value = raw.strip().strip("\"'")
    if "://" in value:
        value = urlsplit(value).path
    value = value.split("?", 1)[0].split("#", 1)[0]
    value = _PARAMETER.sub("{}", value)
    value = _MULTISLASH.sub("/", value)
    if not value.startswith("/"):
        value = "/" + value
    if len(value) > 1:
        value = value.rstrip("/")
    return value or "/"


def join_routes(prefix: str, route: str) -> str:
    if not prefix:
        return canonical_route(route)
    if not route or route == "/":
        return canonical_route(prefix)
    return canonical_route(prefix.rstrip("/") + "/" + route.lstrip("/"))


def http_contract(method: str, route: str) -> str:
    return f"{method.upper()} {canonical_route(route)}"
