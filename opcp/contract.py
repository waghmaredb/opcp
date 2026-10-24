"""Capability contracts (spec section 6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from ._io import ValidationFailed, errors, load_document, schema_validator, validator_for
from .archetypes import EVIDENCE_BY_DEFAULT, archetype_schema
from .rclass import RClass


@dataclass(frozen=True)
class Contract:
    id: str
    version: str
    name: str
    archetype: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    rclass: RClass
    data_classification: str
    evidence_required: bool
    examples: tuple[Mapping[str, Any], ...]
    single_source: bool = False
    service_level: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def major(self) -> int:
        return int(self.version.split(".")[0])

    @property
    def leased_fields(self) -> tuple[str, ...]:
        """Top-level input fields a supplier may receive (the context lease, spec 11.2)."""
        return tuple(self.input_schema.get("properties", {}))

    @classmethod
    def from_dict(cls, doc: Mapping[str, Any]) -> "Contract":
        problems = errors(schema_validator("capability"), doc)
        if problems:
            raise ValidationFailed(f"capability contract {doc.get('id', '?')!r}", problems)
        evidence = doc.get("evidence_required", doc["archetype"] in EVIDENCE_BY_DEFAULT)
        return cls(
            id=doc["id"],
            version=doc["version"],
            name=doc["name"],
            archetype=doc["archetype"],
            description=doc["description"],
            input_schema=doc["input"],
            output_schema=doc["output"],
            rclass=RClass.parse(doc["rclass"]),
            data_classification=doc["data_classification"],
            evidence_required=bool(evidence),
            examples=tuple(doc["examples"]),
            single_source=bool(doc.get("single_source", False)),
            service_level=doc.get("service_level", {}),
            raw=doc,
        )

    @classmethod
    def load(cls, path: str | Path) -> "Contract":
        return cls.from_dict(load_document(path))

    def lease(self, payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Return (leased input, dotted paths of withheld fields).

        Removes every field the input schema does not declare, at any depth (spec 11.2).
        """
        withheld: list[str] = []
        leased = _prune(dict(payload), self.input_schema, "", withheld)
        return leased, sorted(withheld)

    def input_errors(self, payload: Mapping[str, Any], *, redact: bool = False) -> list[str]:
        return errors(validator_for(dict(self.input_schema)), payload, redact=redact)

    def output_errors(self, output: Any) -> list[str]:
        """Errors against both the contract's output schema and its archetype's required fields."""
        found = [f"contract: {e}" for e in errors(validator_for(dict(self.output_schema)), output)]
        found += [f"archetype {self.archetype}: {e}" for e in errors(validator_for(dict(archetype_schema(self.archetype))), output)]
        return found


_COMPOSITE = ("anyOf", "oneOf", "allOf", "$ref", "not", "if", "patternProperties")


def _prune(value: Any, schema: Mapping[str, Any], path: str, withheld: list[str]) -> Any:
    """Keep only what ``schema`` declares, failing closed.

    An object passes whole only if its schema says ``additionalProperties: true``. A field whose
    schema uses composition keywords (``anyOf``, ``$ref`` and the like) is withheld entirely,
    because the reference runtime cannot prove which of its parts are declared.
    """
    if isinstance(schema, Mapping) and any(k in schema for k in _COMPOSITE):
        withheld.append(path or "(input)")
        return _WITHHELD
    if isinstance(value, dict) and isinstance(schema, Mapping):
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties")
        kept = {}
        for key, item in value.items():
            where = f"{path}.{key}" if path else key
            if key in props:
                pruned = _prune(item, props[key], where, withheld)
            elif extra is True:
                pruned = item
            elif isinstance(extra, Mapping):
                pruned = _prune(item, extra, where, withheld)
            else:
                withheld.append(where)
                continue
            if pruned is not _WITHHELD:
                kept[key] = pruned
        return kept
    if isinstance(value, list) and isinstance(schema, Mapping) and isinstance(schema.get("items"), Mapping):
        items = [_prune(item, schema["items"], f"{path}[{i}]", withheld) for i, item in enumerate(value)]
        return [i for i in items if i is not _WITHHELD]
    return value


_WITHHELD = object()


def load_catalogue(directory: str | Path) -> dict[str, Contract]:
    """Load every contract in a directory, keyed by id."""
    contracts: dict[str, Contract] = {}
    for path in sorted(Path(directory).glob("*.y*ml")) + sorted(Path(directory).glob("*.json")):
        contract = Contract.load(path)
        if contract.id in contracts:
            raise ValueError(f"duplicate contract id {contract.id!r} in {path}")
        contracts[contract.id] = contract
    return contracts
