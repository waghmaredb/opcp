"""The library of sources the question bank cites (references/frameworks.yaml)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ._io import load_document
from ._paths import data_dir


@lru_cache(maxsize=1)
def _library() -> dict[str, Any]:
    try:
        path = data_dir("references") / "frameworks.yaml"
    except FileNotFoundError:
        return {}
    return (load_document(path) or {}) if path.exists() else {}


def load_references() -> dict[str, dict[str, Any]]:
    """Sources keyed by id: id, short, title, publisher, date, jurisdiction, type, status, url, verified_via."""
    return {s["id"]: s for s in _library().get("sources", [])}


def portfolio_refs() -> list[dict[str, str]]:
    """References for the portfolio-level concentration view."""
    return list(_library().get("portfolio_refs", []))
