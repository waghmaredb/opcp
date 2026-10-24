"""Append-only event log: the business's record of every request, decision and response (spec 11.1)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterator


class EventLog:
    """Entries are serialised on write, so later changes to the caller's objects cannot alter history."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._lines: list[str] = []

    def append(self, kind: str, trace_id: str, **data: Any) -> None:
        entry = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "kind": kind, "trace_id": trace_id, **data}
        line = json.dumps(entry, sort_keys=True, default=str)
        self._lines.append(line)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def entries(self, trace_id: str | None = None) -> list[dict[str, Any]]:
        items = (json.loads(line) for line in self._lines)
        return [e for e in items if trace_id is None or e["trace_id"] == trace_id]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.entries())

    def __len__(self) -> int:
        return len(self._lines)

    def export_jsonl(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text("".join(line + "\n" for line in self._lines), encoding="utf-8")
        return path
