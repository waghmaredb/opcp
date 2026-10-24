"""Suggested values for regulatory registers, derived from a scorecard assessment.

The scorecard asks about the same things that registers of third-party arrangements record:
substitutability, reintegration, alternative providers, notice periods and end dates. This module
turns an assessment into suggested register values, so a firm can check them against what it
reports instead of answering twice.

Only the EU DORA register of information is supported. Its field codes and closed lists come from
Commission Implementing Regulation (EU) 2024/2956, Annex I. The mapping from OPCP answers to those
values is OPCP's own reasoning, set out in docs/REGISTERS.md. The output is a suggestion for review,
never a filing.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path
from typing import Any, Mapping

from ._io import load_document
from .scorecard import LOCKED, PARTIAL, READY, ProcessResult, Result, evaluate

REGISTERS = ("dora",)

# EU DORA register of information (Implementing Regulation (EU) 2024/2956, Annex I).
SUBSTITUTABILITY = ("Not substitutable", "Highly complex substitutability",
                    "Medium complexity in terms of substitutability", "Easily substitutable")
REINTEGRATION = ("Easy", "Difficult", "Highly complex")

_LOGIC_TO_REINTEGRATION = {"owned": 0, "shared": 1, "vendor_held": 2}
_CONTEXT_TO_REINTEGRATION = {"exportable": 0, "partial": 1, "trapped": 2}
_RANK = {READY: 0, PARTIAL: 1, LOCKED: 2}

DORA_COLUMNS = [
    ("opcp_process_id", "OPCP process ID"),
    ("opcp_process_name", "OPCP process name"),
    ("opcp_supplier", "Supplier (as named in the assessment)"),
    ("B_07.01.0010", "B_07.01.0010 Contractual arrangement reference number"),
    ("B_07.01.0020", "B_07.01.0020 Identification code of the ICT third-party service provider"),
    ("B_07.01.0050", "B_07.01.0050 Substitutability of the ICT third-party service provider"),
    ("B_07.01.0060", "B_07.01.0060 Reason where not substitutable or difficult to be substitutable"),
    ("B_07.01.0080", "B_07.01.0080 Existence of an exit plan"),
    ("B_07.01.0090", "B_07.01.0090 Possibility of reintegration of the contracted ICT service"),
    ("B_07.01.0110", "B_07.01.0110 Are there alternative ICT third-party service providers identified?"),
    ("B_07.01.0120", "B_07.01.0120 Identification of alternative ICT TPP"),
    ("B_02.02.0080", "B_02.02.0080 End date of the contractual arrangement"),
    ("B_02.02.0100", "B_02.02.0100 Notice period for the financial entity (calendar days)"),
    ("opcp_basis", "Basis for the suggested values (OPCP)"),
]


def _assessment(doc: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the scorecard-format assessment for an assessment or an answers file."""
    if "answers_version" in doc:
        from .questionbank import Bank, convert
        assessment, _, _ = convert(Bank.load(), doc)
        return assessment
    return doc


def _measure(pr: ProcessResult, key: str) -> str | None:
    for m in pr.measures:
        if m.key == key:
            return m.rating
    return None


def _recent(drill_date: str | None, on: str) -> bool:
    if not drill_date:
        return False
    try:
        days = (dt.date.fromisoformat(on) - dt.date.fromisoformat(drill_date)).days
    except ValueError:
        return False
    return 0 <= days <= 365


def dora_row(proc: Mapping[str, Any], pr: ProcessResult, assessment_date: str) -> dict[str, Any]:
    """Suggested B_07.01 and B_02.02 values for one process, with the reasoning behind them."""
    basis: list[str] = []
    contract = proc.get("contract", {})
    swap = proc.get("time_to_swap", {})
    fallback = proc.get("fallback_supplier")

    # Reintegration: the harder of bringing the logic back and bringing the context back.
    logic = proc.get("logic_ownership")
    context = proc.get("context_residency")
    level = max(_LOGIC_TO_REINTEGRATION.get(logic, 2), _CONTEXT_TO_REINTEGRATION.get(context, 2))
    reintegration = REINTEGRATION[level]
    basis.append(f"reintegration from logic ownership '{logic}' and context '{context}'")

    # Substitutability: the worst of the measures that decide whether another supplier could take over.
    # "Not substitutable" says the market has no real alternative; that is the firm's judgement, and an
    # alternative not yet identified is not evidence of it, so it is never suggested automatically.
    deciding = {k: _measure(pr, k) for k in ("swap", "debt", "context", "fallback")}
    deciding = {k: r for k, r in deciding.items() if r}
    worst = max((_RANK[r] for r in deciding.values()), default=2)
    substitutability = {2: SUBSTITUTABILITY[1], 1: SUBSTITUTABILITY[2], 0: SUBSTITUTABILITY[3]}[worst]
    drivers = [k for k, r in deciding.items() if _RANK[r] == worst]
    names = {"swap": "time-to-swap", "debt": "lock-in", "context": "context residency", "fallback": "fallback"}
    basis.append(f"substitutability set by {', '.join(names[d] for d in drivers)} rated {[LOCKED, PARTIAL, READY][2 - worst]}"
                 if worst else "substitutability: time-to-swap, lock-in, context and fallback all rated ready")
    if substitutability == SUBSTITUTABILITY[3] and swap.get("confidence") != "proven":
        substitutability = SUBSTITUTABILITY[2]
        basis.append("capped at medium complexity because time-to-swap is estimated, not proven")

    reason = ""
    if substitutability in SUBSTITUTABILITY[:2]:
        lack_of_alternatives = not fallback
        migration = (context != "exportable" or _measure(pr, "debt") != READY
                     or logic == "vendor_held" or _measure(pr, "swap") != READY)
        if lack_of_alternatives and migration:
            reason = "3"
            basis.append("reason 3: no alternative identified, and migration is difficult")
        elif lack_of_alternatives:
            reason = "1"
            basis.append("reason 1: no alternative identified; confirm the market lacks real alternatives")
        else:
            reason = "2"
            basis.append("reason 2: migrating data and workloads is difficult")

    # Exit plan: OPCP does not ask whether a documented plan exists, so suggest Yes only when a
    # rehearsed swap within the last 12 months shows one in practice; otherwise leave it to the firm.
    exit_plan = ""
    if _recent(swap.get("drill_date"), assessment_date):
        exit_plan = "Yes"
        basis.append(f"exit plan supported by a swap drill on {swap['drill_date']}")
    else:
        basis.append("exit plan left blank: no swap drill in the last 12 months; confirm from your records")

    return {
        "opcp_process_id": proc.get("id", ""),
        "opcp_process_name": proc.get("name", ""),
        "opcp_supplier": proc.get("supplier", ""),
        "B_07.01.0010": "",
        "B_07.01.0020": "",
        "B_07.01.0050": substitutability,
        "B_07.01.0060": reason,
        "B_07.01.0080": exit_plan,
        "B_07.01.0090": reintegration,
        "B_07.01.0110": "Yes" if fallback else "No",
        "B_07.01.0120": fallback or "",
        "B_02.02.0080": contract.get("end_date", ""),
        "B_02.02.0100": contract.get("notice_days", ""),
        "opcp_basis": "; ".join(basis),
    }


def dora_rows(doc: Mapping[str, Any], result: Result | None = None) -> list[dict[str, Any]]:
    """Suggested DORA register values for every critical process in an assessment or answers file."""
    assessment = _assessment(doc)
    result = result or evaluate(assessment)
    by_id = {p["id"]: p for p in assessment["processes"]}
    return [dora_row(by_id[pr.id], pr, result.assessment_date) for pr in result.critical if pr.id in by_id]


def render_csv(rows: list[dict[str, Any]], columns=DORA_COLUMNS) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([label for _, label in columns])
    for row in rows:
        writer.writerow([row.get(key, "") for key, _ in columns])
    return out.getvalue()


def export_file(path: str | Path, register: str = "dora") -> str:
    if register not in REGISTERS:
        raise ValueError(f"unknown register {register!r}; supported: {', '.join(REGISTERS)}")
    return render_csv(dora_rows(load_document(path)))
