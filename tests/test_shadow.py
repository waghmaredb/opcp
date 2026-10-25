"""Shadow routing for swap drills (spec 9.5)."""

import datetime as dt
import json

import pytest

from opcp._io import ValidationFailed
from opcp._paths import data_dir
from opcp.adapter import Adapter, AdapterResult, SupplierProfile
from opcp.cli import main
from opcp.contract import load_catalogue
from opcp.demo import TODAY
from opcp.drill import load_jsonl, render_text, summarise
from opcp.eventlog import EventLog
from opcp.gate import AuthorityGate
from opcp.rclass import RClass
from opcp.router import Route, ShadowSpec
from opcp.runtime import ConfigurationError, ControlPlane

CATALOGUE = load_catalogue(data_dir("catalogue"))
PERSON = {"full_name": "Alex Tan", "date_of_birth": "1990-04-12",
          "document": {"type": "passport", "number": "K1234567", "issuing_country": "SG"},
          "marketing_notes": "not part of the contract"}
CALL = dict(process_id="onboarding", step="idv", principal="agent", data_classification="confidential",
            accountable_role="Head of Onboarding")


class Check(Adapter):
    def __init__(self, profile, verdict="pass", fail=False, bad=False, confidence=0.9):
        super().__init__(profile)
        self.verdict, self.fail, self.bad, self.confidence = verdict, fail, bad, confidence
        self.seen = []

    def invoke(self, payload, request):
        self.seen.append(dict(payload))
        if self.fail:
            raise RuntimeError("supplier down")
        output = {"verdict": "maybe"} if self.bad else {"verdict": self.verdict, "reason_codes": []}
        return AdapterResult(output, [{"type": "report", "reference": "r"}], self.confidence, 0.5)


def profile(aid, **kw):
    base = dict(adapter_id=aid, supplier_id=aid.upper(), kind="vendor", capability="verify-identity", contract_major=1,
                register_ref="TPR-1", approved=True, conformance_passed=True, max_data_classification="confidential",
                regions=frozenset({"SG"}), contract_end=dt.date(2030, 1, 1))
    base.update(kw)
    return SupplierProfile(**base)


def route(shadow, candidates=("live",), **kw):
    doc = {"opcp_version": "0.1", "capability": "verify-identity", "version": 1, "mode": "pinned",
           "authored_by": "maker", "approved_by": "checker", "candidates": list(candidates), **kw}
    if shadow is not None:
        doc["shadow"] = shadow
    return Route.from_dict(doc)


def setup(shadow_adapter, shadow=None, gate=None, **kw):
    live = Check(profile("live"))
    r = route(shadow or {"adapter": "alt"})
    log = EventLog()
    plane = ControlPlane(CATALOGUE, [live, shadow_adapter], [r], gate=gate, log=log, today=TODAY, **kw)
    return plane, live, log


def shadow_entries(log):
    return [e for e in log if e["kind"] == "shadow"]


def test_shadow_copies_the_leased_request_and_records_agreement():
    alt = Check(profile("alt"))
    plane, live, log = setup(alt)
    resp = plane.call("verify-identity", PERSON, idempotency_key="k1", **CALL)
    assert resp.status == "ok" and resp.supplier_id == "LIVE"
    assert alt.seen and "marketing_notes" not in alt.seen[0]  # only the leased fields leave
    (entry,) = shadow_entries(log)
    assert entry["outcome"] == "ok" and entry["disagreed"] == []
    assert set(entry["agreed"]) >= {"verdict", "reason_codes"}
    assert "differences" not in entry  # values stay out of the log by default


def test_disagreement_is_recorded_and_never_changes_the_live_result():
    alt = Check(profile("alt"), verdict="refer")
    plane, _, log = setup(alt, store_values=True)
    resp = plane.call("verify-identity", PERSON, idempotency_key="k2", **CALL)
    assert resp.output["verdict"] == "pass"
    (entry,) = shadow_entries(log)
    assert entry["disagreed"] == ["verdict"] or "verdict" in entry["disagreed"]
    assert entry["differences"]["verdict"] == {"live": "pass", "shadow": "refer"}


@pytest.mark.parametrize("kw, outcome", [({"fail": True}, "error"), ({"bad": True}, "invalid")])
def test_shadow_failures_are_recorded_and_the_live_call_succeeds(kw, outcome):
    alt = Check(profile("alt"), **kw)
    plane, _, log = setup(alt)
    assert plane.call("verify-identity", PERSON, idempotency_key="k3", **CALL).status == "ok"
    assert shadow_entries(log)[0]["outcome"] == outcome


@pytest.mark.parametrize("kw, words", [
    ({"approved": False}, "not approved"),
    ({"regions": frozenset({"US"})}, "outside permitted regions"),
    ({"max_data_classification": "internal"}, "not permitted to process confidential"),
])
def test_ineligible_shadow_supplier_never_receives_data(kw, words):
    alt = Check(profile("alt", **kw))
    plane, _, log = setup(alt)
    plane.call("verify-identity", PERSON, idempotency_key="k4", residency=["SG"], **CALL)
    assert alt.seen == []
    (entry,) = shadow_entries(log)
    assert entry["outcome"] == "skipped" and words in entry["reason"]


def test_shadow_never_runs_above_r0():
    alt = Check(profile("alt", max_rclass=RClass.R1))
    live = Check(profile("live", max_rclass=RClass.R1))
    gate = AuthorityGate(overrides={"verify-identity": RClass.R1})
    log = EventLog()
    plane = ControlPlane(CATALOGUE, [live, alt], [route({"adapter": "alt"})], gate=gate, log=log, today=TODAY)
    assert plane.call("verify-identity", PERSON, idempotency_key="k5", **CALL).status == "ok"
    assert alt.seen == []
    assert "only for R0" in shadow_entries(log)[0]["reason"]


def test_replay_does_not_run_the_shadow_again():
    alt = Check(profile("alt"))
    plane, _, log = setup(alt)
    plane.call("verify-identity", PERSON, idempotency_key="k6", **CALL)
    plane.call("verify-identity", PERSON, idempotency_key="k6", **CALL)
    assert len(alt.seen) == 1 and len(shadow_entries(log)) == 1


def test_sampling_is_deterministic_and_partial():
    spec = ShadowSpec("alt", sample=0.3)
    picks = [spec.selects(f"key-{i}") for i in range(1000)]
    assert picks == [spec.selects(f"key-{i}") for i in range(1000)]
    assert 200 < sum(picks) < 400


def test_compare_limits_the_fields_checked():
    alt = Check(profile("alt"), verdict="refer")
    plane, _, log = setup(alt, shadow={"adapter": "alt", "compare": ["reason_codes"]})
    plane.call("verify-identity", PERSON, idempotency_key="k7", **CALL)
    entry = shadow_entries(log)[0]
    assert entry["agreed"] == ["reason_codes"] and entry["disagreed"] == []


def test_route_rules():
    with pytest.raises(ValidationFailed):
        route({"adapter": "live"})                      # the primary cannot shadow itself
    with pytest.raises(ValidationFailed):
        route({"adapter": "alt", "sample": 0})          # sample must be above zero
    with pytest.raises(ConfigurationError):
        ControlPlane(CATALOGUE, [Check(profile("live"))], [route({"adapter": "ghost"})], today=TODAY)


def test_drill_summary_and_cli(tmp_path, capsys):
    agree, differ = Check(profile("alt")), None
    plane, live, log = setup(agree)
    for i in range(4):
        person = {**PERSON, "document": {**PERSON["document"], "number": f"K{i:07d}"}}
        plane.call("verify-identity", person, idempotency_key=f"d{i}", **CALL)
    agree.verdict = "refer"
    agree._results.clear()
    plane.call("verify-identity", {**PERSON, "full_name": "Sam Lee"}, idempotency_key="d9", **CALL)
    (s,) = summarise(log)
    assert (s.compared, s.full_agreement) == (5, 4)
    assert s.to_dict()["field_agreement"]["verdict"] == pytest.approx(0.8)
    assert "full agreement 4 (80.0%)" in render_text([s])

    path = log.export_jsonl(tmp_path / "events.jsonl")
    assert summarise(load_jsonl(path))[0].compared == 5
    assert main(["shadow-report", str(path)]) == 0
    assert "shadow supplier alt" in capsys.readouterr().out
    assert main(["shadow-report", str(path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["full_agreement"] == 4


def test_an_empty_event_log_passed_in_is_the_one_used():
    # Regression: an empty EventLog is falsy, and `log or EventLog()` silently replaced it.
    log = EventLog()
    plane = ControlPlane(CATALOGUE, [Check(profile("live"))], [route(None)], log=log, today=TODAY)
    assert plane.log is log
