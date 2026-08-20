"""Athena CodeGraph public package."""

import os
from importlib.metadata import PackageNotFoundError, version


def _runtime_version() -> str:
    image_version = os.getenv("ATHENA_VERSION", "").strip()
    if image_version:
        return image_version
    try:
        return version("athena-codegraph")
    except PackageNotFoundError:  # pragma: no cover - source tree without installation metadata
        return "0.2.0"


__version__ = _runtime_version()
