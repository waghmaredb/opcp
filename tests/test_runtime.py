import datetime as dt
import socket

import pytest

from opcp._paths import data_dir
from opcp.adapter import Adapter, AdapterResult, SupplierProfile
from opcp.contract import Contract, load_catalogue
from opcp.demo import TODAY, build
from opcp.envelope import Request
from opcp.eventlog import EventLog
from opcp.gate import Approval, AuthorityGate
from opcp.rclass import RClass
from opcp.router import Route, concentration, exclusion_reasons
from opcp.runtime import ConfigurationError, ControlPlane
from opcp._io import ValidationFailed

CATALOGUE = load_catalogue(data_dir("catalogue"))
IDV = CATALOGUE["verify-identity"]
PERSON = {"full_name": "Alex Tan", "date_of_birth": "1990-04-12",
          "document": {"type": "passport", "number": "K1234567", "issuing_country": "SG"}}
CALL = dict(process_id="onboarding", step="idv", principal="agent", data_classification="confidential",
            accountable_role="Head of Onboarding")


class Fixed(Adapter):
    """Returns a fixed check result, or raises."""

    def __init__(self, profile, confidence=0.9, fail=False, bad=False):
        super().__init__(profile)
        self.confidence, self.fail, self.bad = confidence, fail, bad
        self.seen = []

    def invoke(self, payload, request):
        self.seen.append(dict(payload))
        if self.fail:
            raise RuntimeError("supplier down")
        output = {"verdict": "maybe"} if self.bad else {"verdict": "pass", "reason_codes": []}
        return AdapterResult(output, [{"type": "report", "reference": "r1"}], self.confidence, 1.0)


def profile(aid, **kw):
    base = dict(adapter_id=aid, supplier_id=aid.upper(), kind="vendor", capability="verify-identity", contract_major=1,
                register_ref="TPR-1", approved=True, conformance_passed=True, max_data_classification="confidential",
                regions=frozenset({"SG"}), contract_end=dt.date(2030, 1, 1))
    base.update(kw)
    return SupplierProfile(**base)


def route(candidates, mode="pinned", **kw):
    doc = {"opcp_version": "0.1", "capability": "verify-identity", "version": 1, "mode": mode,
           "authored_by": "maker", "approved_by": "checker", "candidates": candidates, **kw}
    return Route.from_dict(doc)


def plane(adapters, r, **kw):
    return ControlPlane(CATALOGUE, adapters, [r], today=TODAY, **kw)


# ------------------------------------------------------------ contracts


def test_catalogue_loads_and_validates():
    assert {"verify-identity", "extract-document-fields", "send-customer-notification",
            "post-journal-entry", "review-identity-exception"} <= set(CATALOGUE)
    assert IDV.archetype == "check" and IDV.rclass is RClass.R0 and IDV.evidence_required


def test_contract_rejects_unknown_archetype():
    doc = dict(IDV.raw, archetype="teleport")
    with pytest.raises(ValidationFailed):
        Contract.from_dict(doc)


def test_archetype_fields_enforced_beyond_contract_schema():
    assert IDV.output_errors({"verdict": "pass"})  # reason_codes missing
    assert not IDV.output_errors({"verdict": "pass", "reason_codes": []})


# ------------------------------------------------------------ lease, gate, fail closed


def test_context_lease_withholds_undeclared_fields():
    a = Fixed(profile("a"))
    p = plane([a], route(["a"]))
    r = p.call("verify-identity", {**PERSON, "salary": 999999}, idempotency_key="k1", **CALL)
    assert r.ok
    assert "salary" not in a.seen[0]
    req = [e for e in p.log.entries(r.trace_id) if e["kind"] == "request"][0]
    assert req["withheld_fields"] == ["salary"]
    assert req["request"]["input"]["full_name"] == "<withheld>"  # values not stored by default


def test_unknown_capability_fails_closed_as_r4():
    p = plane([Fixed(profile("a"))], route(["a"]))
    r = p.call("wire-money", {}, idempotency_key="k", **CALL)
    assert r.status == "rejected" and r.rclass == "R4"


def test_gate_runs_before_any_supplier():
    contracts = dict(CATALOGUE)

    class Spy(Adapter):
        called = False

        def invoke(self, payload, request):
            Spy.called = True
            return AdapterResult({"message_id": "m", "delivery_status": "sent"}, [{"type": "x", "reference": "y"}])

    spy = Spy(profile("n", capability="send-customer-notification", max_rclass=RClass.R4))
    r = Route.from_dict({"opcp_version": "0.1", "capability": "send-customer-notification", "version": 1, "mode": "pinned",
                         "authored_by": "maker", "approved_by": "checker", "candidates": ["n"]})
    p = ControlPlane(contracts, [spy], [r], today=TODAY)
    resp = p.call("send-customer-notification", {"recipient_ref": "C1", "channel": "email", "template_id": "t"},
                  idempotency_key="k", **CALL)
    assert resp.status == "rejected" and resp.rclass == "R4"
    assert Spy.called is False


def test_r4_two_person_rule():
    gate = AuthorityGate(approver=lambda *a: Approval(True, by="alice"), two_person_r4=True)
    contract = CATALOGUE["send-customer-notification"]
    req = Request("x", "1", "p", "s", "u", {}, "internal", "k")
    assert not gate.decide(contract, req).allowed
    gate.approver = lambda *a: Approval(True, by="alice", second_by="bob")
    res = gate.decide(contract, req)
    assert res.allowed and res.approved_by == ("alice", "bob")


def test_r2_budget_then_approval():
    gate = AuthorityGate(budgets={"post-journal-entry": 1})
    contract = CATALOGUE["post-journal-entry"]
    req = Request("x", "1", "p", "s", "u", {}, "internal", "k")
    assert gate.decide(contract, req).allowed
    assert not gate.decide(contract, req).allowed  # budget spent, no approver


def test_override_cannot_lower_class():
    gate = AuthorityGate(overrides={"send-customer-notification": RClass.R1})
    with pytest.raises(ValueError):
        gate.class_for(CATALOGUE["send-customer-notification"])


# ------------------------------------------------------------ routing


@pytest.mark.parametrize("change,reason", [
    (dict(approved=False), "not approved"),
    (dict(contract_end=dt.date(2020, 1, 1)), "contract ended"),
    (dict(conformance_passed=False), "conformance"),
    (dict(max_data_classification="internal"), "not permitted to process confidential"),
    (dict(regions=frozenset({"SG", "US"})), "outside permitted regions"),
    (dict(regions=frozenset()), "regions not declared"),
])
def test_each_eligibility_filter(change, reason):
    a = Fixed(profile("a", **change))
    req = Request("verify-identity", "1.0.0", "p", "s", "u", {}, "confidential", "k", residency=("SG",))
    reasons = exclusion_reasons(a, IDV, req, TODAY)
    assert any(reason in r for r in reasons), reasons


def test_rclass_authority_filter():
    ledger = CATALOGUE["post-journal-entry"]
    a = Fixed(profile("a", capability="post-journal-entry", max_rclass=RClass.R1, max_data_classification="internal"))
    req = Request("post-journal-entry", "1.0.0", "p", "s", "u", {}, "internal", "k")
    assert any("not authorised for R2" in r for r in exclusion_reasons(a, ledger, req, TODAY))


def test_pinned_fails_over_on_error_and_invalid_output():
    down, bad, good = Fixed(profile("down"), fail=True), Fixed(profile("bad"), bad=True), Fixed(profile("good"))
    p = plane([down, bad, good], route(["down", "bad", "good"]))
    r = p.call("verify-identity", PERSON, idempotency_key="k", **CALL)
    assert r.ok and r.supplier_id == "GOOD"
    outcomes = [e["outcome"] for e in p.log.entries(r.trace_id) if e["kind"] == "attempt"]
    assert outcomes == ["error", "invalid", "ok"]


def test_cascade_escalates_to_human_when_not_confident():
    low = Fixed(profile("low"), confidence=0.5)
    human = Fixed(profile("human", kind="human", register_ref=None), confidence=None)
    p = plane([low, human], route(["low"], mode="cascade", cascade_min_confidence=0.8, escalation="human"))
    r = p.call("verify-identity", PERSON, idempotency_key="k", **CALL)
    assert r.status == "escalated" and r.supplier_id == "HUMAN"


def test_segmented_route_uses_segment_list():
    a, b = Fixed(profile("a")), Fixed(profile("b"))
    p = plane([a, b], route(["a"], mode="segmented", segments={"MY": ["b"]}))
    assert p.call("verify-identity", PERSON, idempotency_key="k1", segment="MY", **CALL).supplier_id == "B"
    assert p.call("verify-identity", PERSON, idempotency_key="k2", segment="SG", **CALL).supplier_id == "A"


def test_best_score_refused_above_r1():
    ledger = CATALOGUE["post-journal-entry"]

    class L(Adapter):
        def invoke(self, payload, request):
            return AdapterResult({"receipt_id": "r", "status": "completed", "compensation": "reverse"}, [{"type": "a", "reference": "b"}])

    a = L(profile("l", capability="post-journal-entry", max_rclass=RClass.R2, max_data_classification="internal"))
    r = Route.from_dict({"opcp_version": "0.1", "capability": "post-journal-entry", "version": 1, "mode": "best_score",
                         "authored_by": "maker", "approved_by": "checker", "candidates": ["l"]})
    p = ControlPlane({"post-journal-entry": ledger}, [a], [r], gate=AuthorityGate(budgets={"post-journal-entry": 5}), today=TODAY)
    resp = p.call("post-journal-entry", {"entry_date": "2026-10-31", "currency": "SGD",
                                         "lines": [{"account": "1", "debit": 1, "credit": 0}, {"account": "2", "debit": 0, "credit": 1}]},
                  process_id="close", step="s", principal="u", data_classification="internal", idempotency_key="k",
                  accountable_role="Controller")
    assert resp.status == "failed" and "best_score" in resp.error


def test_weighted_choice_is_deterministic_per_key():
    a, b = Fixed(profile("a")), Fixed(profile("b"))
    p = plane([a, b], route(["a", "b"], mode="weighted", weights={"a": 1, "b": 1}))
    first = p.call("verify-identity", PERSON, idempotency_key="same", **CALL)
    p2 = plane([Fixed(profile("a")), Fixed(profile("b"))], route(["a", "b"], mode="weighted", weights={"a": 1, "b": 1}))
    assert p2.call("verify-identity", PERSON, idempotency_key="same", **CALL).supplier_id == first.supplier_id


def test_idempotency_does_not_repeat_effect():
    a = Fixed(profile("a"))
    p = plane([a], route(["a"]))
    r1 = p.call("verify-identity", PERSON, idempotency_key="dup", **CALL)
    r2 = p.call("verify-identity", PERSON, idempotency_key="dup", **CALL)
    assert r1 is r2 and a.invocations == 1


def test_maker_checker_required():
    with pytest.raises(ValidationFailed):
        route(["a"], authored_by="same", approved_by="same")


def test_concentration_limit_blocks_configuration():
    a = Fixed(profile("a"))
    l = Fixed(profile("l", supplier_id="A", capability="post-journal-entry", max_rclass=RClass.R2))
    r1 = route(["a"], critical=True)
    r2 = Route.from_dict({"opcp_version": "0.1", "capability": "post-journal-entry", "version": 1, "mode": "pinned",
                          "critical": True, "authored_by": "m", "approved_by": "c", "candidates": ["l"]})
    assert concentration([r1, r2], {"a": a, "l": l}, 0.5)[0].share == 1.0
    with pytest.raises(ConfigurationError):
        ControlPlane(CATALOGUE, [a, l], [r1, r2], concentration_limit=0.5, today=TODAY)


def test_unknown_adapter_in_route_is_a_configuration_error():
    with pytest.raises(ConfigurationError):
        plane([], route(["ghost"]))


def test_event_log_is_append_only_snapshot(tmp_path):
    log = EventLog(tmp_path / "events.jsonl")
    data = {"x": 1}
    log.append("k", "t", data=data)
    data["x"] = 2
    assert log.entries()[0]["data"] == {"x": 1}
    assert (tmp_path / "events.jsonl").read_text().count("\n") == 1


def test_demo_runs_without_network(monkeypatch):
    def no_network(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "socket", no_network)
    lines = []
    from opcp.demo import run
    run(out=lines.append)
    text = "\n".join(lines)
    assert "escalated" in text and "fails closed" in text and "withheld" in text
