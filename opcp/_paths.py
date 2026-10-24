"""Locate bundled data (schemas, catalogue, examples) from a source checkout or an installed wheel."""

from __future__ import annotations

from pathlib import Path

_PKG = Path(__file__).resolve().parent


def data_dir(name: str) -> Path:
    """Return the directory for `schema`, `catalogue` or `examples`."""
    installed = _PKG / "_data" / name
    if installed.is_dir():
        return installed
    source = _PKG.parent / name
    if source.is_dir():
        return source
    raise FileNotFoundError(f"OPCP data directory not found: {name}")
