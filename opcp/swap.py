"""Supplier swap-drill primitives.

The swap drill is deliberately independent of a supplier SDK. It compares the
results of two adapters against the same business test set and returns an
exportable decision record. A later runtime integration can feed real adapter
outputs into these functions without changing the evaluation semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SwapCase:
    case_id: str
    expected: str
    incumbent: str
    candidate: str
    incumbent_confidence: float | None = None
    candidate_confidence: float | None = None


@dataclass(frozen=True)
class SwapResult:
    capability: str
    incumbent: str
    candidate: str
    process_unchanged: bool
    context_lease_unchanged: bool
    authority_policy_unchanged: bool
    contract_conformance: bool
    regression_pass: bool
    material_exception_regression: bool
    cases: tuple[SwapCase, ...]
    started_at: str
    completed_at: str
    measured_seconds: float

    @property
    def passed(self) -> bool:
        return all(
            (
                self.process_unchanged,
                self.context_lease_unchanged,
                self.authority_policy_unchanged,
                self.contract_conformance,
                self.regression_pass,
                self.material_exception_regression,
            )
        )

    def evidence(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "incumbent": self.incumbent,
            "candidate": self.candidate,
            "decision": "passed" if self.passed else "failed",
            "invariants": {
                "process_unchanged": self.process_unchanged,
                "context_lease_unchanged": self.context_lease_unchanged,
                "authority_policy_unchanged": self.authority_policy_unchanged,
                "contract_conformance": self.contract_conformance,
            },
            "regression": {
                "passed": self.regression_pass,
                "cases": len(self.cases),
                "material_exception_regression": self.material_exception_regression,
            },
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "measured_seconds": self.measured_seconds,
            "measured_time_to_swap_hours": round(self.measured_seconds / 3600, 3),
            "cases": [asdict(case) for case in self.cases],
        }


def evaluate_swap(
    *,
    capability: str,
    incumbent: str,
    candidate: str,
    cases: Sequence[SwapCase],
    process_unchanged: bool = True,
    context_lease_unchanged: bool = True,
    authority_policy_unchanged: bool = True,
    contract_conformance: bool = True,
    started_at: str | None = None,
    completed_at: str | None = None,
    measured_seconds: float = 0.0,
) -> SwapResult:
    """Evaluate a candidate supplier against the incumbent.

    A case passes when the candidate preserves the incumbent's expected
    business outcome. The candidate is never promoted merely because its
    output is structurally valid: business regression is a separate gate.
    """
    regression_pass = all(case.candidate == case.expected for case in cases)
    material_exception_regression = all(
        not (case.expected in {"fail", "refer"} and case.candidate != case.expected)
        for case in cases
    )
    now = datetime.now(timezone.utc).isoformat()
    return SwapResult(
        capability=capability,
        incumbent=incumbent,
        candidate=candidate,
        process_unchanged=process_unchanged,
        context_lease_unchanged=context_lease_unchanged,
        authority_policy_unchanged=authority_policy_unchanged,
        contract_conformance=contract_conformance,
        regression_pass=regression_pass,
        material_exception_regression=material_exception_regression,
        cases=tuple(cases),
        started_at=started_at or now,
        completed_at=completed_at or now,
        measured_seconds=measured_seconds,
    )
