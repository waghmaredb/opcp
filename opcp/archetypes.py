"""The seven capability archetypes and the output fields each one requires (spec section 5)."""

from __future__ import annotations

from typing import Any, Mapping

ARCHETYPE_OUTPUT: dict[str, dict[str, Any]] = {
    "check": {
        "required": ["verdict", "reason_codes"],
        "properties": {
            "verdict": {"enum": ["pass", "fail", "refer"]},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
        },
    },
    "extract": {
        "required": ["fields", "field_confidence"],
        "properties": {
            "fields": {"type": "object"},
            "field_confidence": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}},
        },
    },
    "generate": {
        "required": ["draft", "review_status"],
        "properties": {
            "draft": {"type": "string"},
            "review_status": {"enum": ["pending", "approved", "rejected"]},
        },
    },
    "transact": {
        "required": ["receipt_id", "status", "compensation"],
        "properties": {
            "receipt_id": {"type": "string"},
            "status": {"enum": ["completed", "pending", "failed"]},
            "compensation": {"type": "string", "minLength": 1},
        },
    },
    "retrieve": {
        "required": ["records", "as_of"],
        "properties": {"records": {"type": "array"}, "as_of": {"type": "string"}},
    },
    "notify": {
        "required": ["message_id", "delivery_status"],
        "properties": {
            "message_id": {"type": "string"},
            "delivery_status": {"enum": ["queued", "sent", "delivered", "failed"]},
        },
    },
    "human_task": {
        "required": ["outcome", "assignee_role", "completed_at"],
        "properties": {
            "outcome": {"type": "string"},
            "assignee_role": {"type": "string"},
            "completed_at": {"type": "string"},
        },
    },
}

ARCHETYPES = tuple(ARCHETYPE_OUTPUT)

# Archetypes whose responses require evidence unless a contract says otherwise.
EVIDENCE_BY_DEFAULT = {"check", "transact"}


def archetype_schema(archetype: str) -> Mapping[str, Any]:
    """JSON Schema fragment every response output of this archetype must satisfy."""
    try:
        spec = ARCHETYPE_OUTPUT[archetype]
    except KeyError as exc:
        raise ValueError(f"unknown archetype: {archetype!r}") from exc
    return {"type": "object", "required": spec["required"], "properties": spec["properties"]}
