"""Loading YAML or JSON documents and validating them against the bundled schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from ._paths import data_dir


class _StringDateLoader(yaml.SafeLoader):
    """SafeLoader that keeps dates and timestamps as strings, so they validate as JSON strings."""


_StringDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_document(path: str | Path) -> Any:
    """Load a YAML or JSON file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.load(text, Loader=_StringDateLoader)  # noqa: S506 - safe loader subclass


@lru_cache(maxsize=None)
def schema_validator(name: str) -> Draft202012Validator:
    """Validator for a bundled schema, e.g. ``capability``, ``route``, ``scorecard``."""
    schema = json.loads((data_dir("schema") / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validator_for(schema: dict) -> Draft202012Validator:
    """Validator for an ad hoc schema, such as a contract's input or output."""
    return Draft202012Validator(schema, format_checker=FormatChecker())


def errors(validator: Draft202012Validator, document: Any, *, redact: bool = False) -> list[str]:
    """Human-readable validation errors, with the path to each offending field.

    With ``redact=True`` the message names only the field and the rule it broke, never the value,
    so it is safe to write to a log that must not hold input values.
    """
    found = []
    for err in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "(document)"
        found.append(f"{where}: fails '{err.validator}' rule" if redact else f"{where}: {err.message}")
    return found


class ValidationFailed(ValueError):
    """A document did not validate. ``problems`` lists each error."""

    def __init__(self, what: str, problems: list[str]):
        self.problems = problems
        super().__init__(f"{what} is not valid:\n  - " + "\n  - ".join(problems))
