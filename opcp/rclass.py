"""Reversibility Classes R0-R4 and the default autonomy policy.

Mirrors "Reversibility Classes for Agent Actions" v0.1, sections 4 and 8
(https://github.com/TwoMuchLabs/reversibility-classes). Kept local until that
package is published, so OPCP installs without a source dependency.
"""

from __future__ import annotations

from enum import Enum, IntEnum


class RClass(IntEnum):
    R0 = 0  # No effect outside the working context
    R1 = 1  # Restorable with ordinary effort
    R2 = 2  # Compensable at bounded cost
    R3 = 3  # Hard to recover
    R4 = 4  # Irreversible

    @classmethod
    def parse(cls, value: "str | int | RClass") -> "RClass":
        if isinstance(value, RClass):
            return value
        if isinstance(value, int):
            return cls(value)
        text = str(value).strip().upper()
        if text in cls.__members__:
            return cls[text]
        raise ValueError(f"not a Reversibility Class: {value!r}")

    def __str__(self) -> str:
        return self.name


class Decision(str, Enum):
    ALLOW = "allow"
    ALLOW_AND_NOTIFY = "allow_notify"
    APPROVE_OR_BUDGET = "approve_or_budget"
    APPROVE_EACH = "approve_each"
    NEVER_AUTONOMOUS = "never_autonomous"


DEFAULT_POLICY: dict[RClass, Decision] = {
    RClass.R0: Decision.ALLOW,
    RClass.R1: Decision.ALLOW_AND_NOTIFY,
    RClass.R2: Decision.APPROVE_OR_BUDGET,
    RClass.R3: Decision.APPROVE_EACH,
    RClass.R4: Decision.NEVER_AUTONOMOUS,
}
