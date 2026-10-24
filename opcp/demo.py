"""A runnable walk-through with simulated suppliers. No network calls; all suppliers are fictional."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any

from ._paths import data_dir
from .adapter import Adapter, AdapterResult, SupplierProfile
from .contract import load_catalogue
from .envelope import Request
from .eventlog import EventLog
from .gate import Approval, AuthorityGate
from .rclass import RClass
from .router import Route
from .runtime import ControlPlane

TODAY = dt.date(2026, 10, 24)


def _score(text: str, salt: str) -> float:
    """Deterministic pseudo-score in [0, 1) so the demo is repeatable."""
    return int(hashlib.sha256((salt + text).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


class SimulatedIdentityVendor(Adapter):
    """A fictional identity-verification vendor whose confidence varies by case."""

    def __init__(self, profile: SupplierProfile, bias: float):
        super().__init__(profile)
        self.bias = bias

    def invoke(self, payload: dict[str, Any], request: Request) -> AdapterResult:
        confidence = round(min(0.99, self.bias + 0.25 * _score(payload["document"]["number"], self.profile.supplier_id)), 2)
        verdict = "pass" if confidence >= 0.6 else "refer"
        return AdapterResult(
            output={"verdict": verdict, "reason_codes": [] if verdict == "pass" else ["LOW_MATCH"], "match_score": confidence},
            evidence=[{"type": "vendor_report", "reference": f"{self.profile.supplier_id}:{request.trace_id[:8]}"}],
            confidence=confidence,
            cost=self.profile.cost_per_call,
        )


class ReviewerTeam(Adapter):
    """Human reviewers fulfilling the same Check contract as the last step of a cascade."""

    def invoke(self, payload: dict[str, Any], request: Request) -> AdapterResult:
        return AdapterResult(
            output={"verdict": "pass", "reason_codes": ["MANUAL_REVIEW"]},
            evidence=[{"type": "reviewer_note", "reference": f"case:{request.trace_id[:8]}"}],
            confidence=None,
            cost=self.profile.cost_per_call,
        )


class SimulatedLedger(Adapter):
    def invoke(self, payload: dict[str, Any], request: Request) -> AdapterResult:
        receipt = "JE-" + hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:8].upper()
        return AdapterResult(
            output={"receipt_id": receipt, "status": "completed", "compensation": f"post a reversing entry for {receipt}"},
            evidence=[{"type": "ledger_receipt", "reference": receipt}],
        )


class SimulatedMessenger(Adapter):
    def invoke(self, payload: dict[str, Any], request: Request) -> AdapterResult:
        return AdapterResult(output={"message_id": "MSG-" + request.trace_id[:8], "delivery_status": "queued"},
                             evidence=[{"type": "provider_receipt", "reference": request.trace_id[:8]}])


def build(approver=None) -> ControlPlane:
    contracts = load_catalogue(data_dir("catalogue"))
    common = dict(capability="verify-identity", contract_major=1, approved=True, conformance_passed=True,
                  max_data_classification="confidential", contract_end=dt.date(2027, 12, 31))
    adapters = [
        SimulatedIdentityVendor(SupplierProfile("idv-alpha", "Alpha ID (fictional)", "vendor", register_ref="TPR-0101",
                                                regions=frozenset({"SG"}), cost_per_call=1.20, quality={"default": 0.92}, **common), bias=0.62),
        SimulatedIdentityVendor(SupplierProfile("idv-beta", "Beta Verify (fictional)", "vendor", register_ref="TPR-0102",
                                                regions=frozenset({"SG", "MY"}), cost_per_call=0.45, quality={"default": 0.84}, **common), bias=0.45),
        SimulatedIdentityVendor(SupplierProfile("idv-gamma", "Gamma KYC (fictional)", "vendor", register_ref="TPR-0199",
                                                regions=frozenset({"US"}), cost_per_call=0.30, quality={"default": 0.88}, **common), bias=0.7),
        SimulatedIdentityVendor(SupplierProfile("idv-delta", "Delta Identity (fictional)", "vendor", register_ref="TPR-0200",
                                                regions=frozenset({"SG"}), cost_per_call=0.25, quality={"default": 0.9},
                                                **{**common, "approved": False}), bias=0.8),
        ReviewerTeam(SupplierProfile("idv-reviewers", "Onboarding review team", "human", regions=frozenset({"SG"}),
                                     cost_per_call=6.0, **common)),
        SimulatedLedger(SupplierProfile("ledger-core", "Core ledger (internal)", "internal", capability="post-journal-entry",
                                        contract_major=1, approved=True, conformance_passed=True, regions=frozenset({"SG"}),
                                        max_rclass=RClass.R2, max_data_classification="internal")),
        SimulatedMessenger(SupplierProfile("notify-omega", "Omega Messaging (fictional)", "vendor", register_ref="TPR-0300",
                                           capability="send-customer-notification", contract_major=1, approved=True,
                                           conformance_passed=True, regions=frozenset({"SG"}), max_rclass=RClass.R4,
                                           max_data_classification="confidential")),
    ]
    routes = [
        Route.from_dict({"opcp_version": "0.1", "capability": "verify-identity", "version": 3, "mode": "cascade",
                         "critical": True, "authored_by": "ops.architect", "approved_by": "risk.officer",
                         "candidates": ["idv-beta", "idv-alpha", "idv-gamma", "idv-delta"],
                         "cascade_min_confidence": 0.75, "escalation": "idv-reviewers"}),
        Route.from_dict({"opcp_version": "0.1", "capability": "post-journal-entry", "version": 1, "mode": "pinned",
                         "critical": True, "authored_by": "finance.ops", "approved_by": "controller", "candidates": ["ledger-core"]}),
        Route.from_dict({"opcp_version": "0.1", "capability": "send-customer-notification", "version": 1, "mode": "pinned",
                         "critical": False, "authored_by": "cx.lead", "approved_by": "risk.officer", "candidates": ["notify-omega"]}),
    ]
    gate = AuthorityGate(approver=approver, budgets={"post-journal-entry": 1})
    return ControlPlane(contracts, adapters, routes, gate=gate, log=EventLog(), concentration_limit=0.75, today=TODAY)


def run(out=print) -> ControlPlane:
    plane = build()
    common = dict(principal="onboarding-agent", data_classification="confidential", residency=["SG"],
                  accountable_role="Head of Retail Onboarding")

    def show(title: str, response) -> None:
        out(f"\n{title}")
        out(f"  status    : {response.status}  ({response.rclass})")
        out(f"  supplier  : {response.supplier_id or '-'}")
        out(f"  route     : {response.route_mode}: {response.route_reason}")
        if response.output:
            out(f"  output    : {response.output}")
        if response.error:
            out(f"  reason    : {response.error}")
        for entry in plane.log.entries(response.trace_id):
            if entry["kind"] == "route" and entry["excluded"]:
                for adapter, reasons in entry["excluded"].items():
                    out(f"  excluded  : {adapter}: {'; '.join(reasons)}")
            if entry["kind"] == "attempt" and entry["outcome"] != "ok":
                out(f"  tried     : {entry['adapter']}: {entry['outcome'].replace('_', ' ')}"
                    + (f" ({entry['confidence']})" if entry.get("confidence") is not None else ""))
            if entry["kind"] == "request" and entry.get("withheld_fields"):
                out(f"  withheld  : {', '.join(entry['withheld_fields'])} (not in the contract, never sent)")

    out("OPCP reference runtime demo (simulated suppliers, no network)")
    out("=" * 62)
    for n, (name, number) in enumerate([("Alex Tan", "K1234567"), ("Priya Nair", "E7654321")], start=1):
        r = plane.call("verify-identity",
                       {"full_name": name, "date_of_birth": "1990-04-12",
                        "document": {"type": "passport", "number": number, "issuing_country": "SG"},
                        "marketing_segment": "affluent"},
                       process_id="customer-onboarding", step="verify-identity", idempotency_key=f"onb-{n}", **common)
        show(f"{n}. Verify identity for {name} (cascade, Singapore data only)", r)

    r = plane.call("post-journal-entry",
                   {"entry_date": "2026-10-31", "currency": "SGD",
                    "lines": [{"account": "6100", "debit": 1200.0, "credit": 0}, {"account": "2100", "debit": 0, "credit": 1200.0}]},
                   process_id="month-end-close", step="accrual", principal="close-agent", data_classification="internal",
                   idempotency_key="je-1", accountable_role="Financial Controller")
    show("3. Post a journal entry (R2, within a pre-approved budget of one)", r)
    r = plane.call("post-journal-entry",
                   {"entry_date": "2026-10-31", "currency": "SGD",
                    "lines": [{"account": "6200", "debit": 300.0, "credit": 0}, {"account": "2100", "debit": 0, "credit": 300.0}]},
                   process_id="month-end-close", step="accrual", principal="close-agent", data_classification="internal",
                   idempotency_key="je-2", accountable_role="Financial Controller")
    show("4. Post a second journal entry (budget used up, no approver configured)", r)
    r = plane.call("send-customer-notification",
                   {"recipient_ref": "CUST-000123", "channel": "email", "template_id": "onboarding-complete-v2"},
                   process_id="customer-onboarding", step="welcome", principal="onboarding-agent",
                   data_classification="confidential", idempotency_key="msg-1", accountable_role="Head of Retail Onboarding")
    show("5. Email the customer (R4: never autonomous)", r)
    r = plane.call("open-bank-account", {}, process_id="customer-onboarding", step="open", principal="onboarding-agent",
                   data_classification="internal", idempotency_key="acct-1")
    show("6. Call a capability with no contract (fails closed as R4)", r)
    out(f"\nEvent log: {len(plane.log)} entries recorded. Export with ControlPlane.log.export_jsonl(path).")
    return plane


if __name__ == "__main__":
    run()
