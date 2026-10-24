"""Suggested DORA register values (docs/REGISTERS.md)."""

import copy
import csv
import io

from opcp._io import load_document
from opcp._paths import data_dir
from opcp.cli import main
from opcp.registers import DORA_COLUMNS, SUBSTITUTABILITY, dora_rows, render_csv

ANSWERS = load_document(data_dir("examples") / "example-bank-answers.yaml")
ASSESSMENT = load_document(data_dir("examples") / "example-bank.yaml")


def by_id(rows):
    return {r["opcp_process_id"]: r for r in rows}


def test_example_answers_give_expected_suggestions():
    rows = by_id(dora_rows(copy.deepcopy(ANSWERS)))
    assert set(rows) == {"onboarding-idv", "payments-sanctions", "customer-notifications"}

    idv = rows["onboarding-idv"]
    assert idv["B_07.01.0050"] == "Highly complex substitutability"
    assert idv["B_07.01.0060"] == "3"            # no alternative, and migration is difficult
    assert idv["B_07.01.0090"] == "Highly complex"  # logic held by the vendor
    assert idv["B_07.01.0110"] == "No" and idv["B_07.01.0120"] == ""
    assert idv["B_07.01.0080"] == ""             # no drill: left for the firm
    assert idv["B_02.02.0080"] == "2027-06-30" and idv["B_02.02.0100"] == 180

    notify = rows["customer-notifications"]
    assert notify["B_07.01.0050"] == "Easily substitutable"  # ready and proven by a drill
    assert notify["B_07.01.0080"] == "Yes"
    assert notify["B_07.01.0120"] == "Vendor E (fictional)"


def test_not_substitutable_is_never_suggested():
    doc = copy.deepcopy(ANSWERS)
    for p in doc["processes"]:
        p["answers"]["ERS-DEP-02"] = {"value": ""}
    for row in dora_rows(doc):
        assert row["B_07.01.0050"] != SUBSTITUTABILITY[0]


def test_easily_substitutable_needs_a_proven_time_to_swap():
    doc = copy.deepcopy(ANSWERS)
    notify = next(p for p in doc["processes"] if p["id"] == "customer-notifications")
    del notify["answers"]["ERS-EXT-04"]  # no drill: the estimate stands
    row = by_id(dora_rows(doc))["customer-notifications"]
    assert row["B_07.01.0050"] == "Medium complexity in terms of substitutability"
    assert "capped at medium" in row["opcp_basis"]
    assert row["B_07.01.0080"] == ""


def test_old_drill_does_not_support_an_exit_plan():
    doc = copy.deepcopy(ANSWERS)
    notify = next(p for p in doc["processes"] if p["id"] == "customer-notifications")
    notify["answers"]["ERS-EXT-04"]["value"] = "2025-01-10"  # more than 12 months before the assessment
    assert by_id(dora_rows(doc))["customer-notifications"]["B_07.01.0080"] == ""


def test_assessment_files_work_too():
    rows = dora_rows(copy.deepcopy(ASSESSMENT))
    assert rows and all(r["B_07.01.0050"] in SUBSTITUTABILITY[1:] for r in rows)


def test_csv_has_the_regulation_field_codes_and_a_basis():
    text = render_csv(dora_rows(copy.deepcopy(ANSWERS)))
    header = next(csv.reader(io.StringIO(text)))
    assert header == [label for _, label in DORA_COLUMNS]
    for code in ("B_07.01.0050", "B_07.01.0060", "B_07.01.0080", "B_07.01.0090", "B_07.01.0110", "B_07.01.0120",
                 "B_02.02.0080", "B_02.02.0100"):
        assert any(h.startswith(code + " ") for h in header), code
    assert header[-1].startswith("Basis")


def test_cli_export_refuses_to_overwrite(tmp_path, capsys):
    src = data_dir("examples") / "example-bank-answers.yaml"
    out = tmp_path / "dora.csv"
    assert main(["scorecard", "export", str(src), "-o", str(out)]) == 0
    assert "not a filing" in capsys.readouterr().out
    assert main(["scorecard", "export", str(src), "-o", str(out)]) == 1
    assert main(["scorecard", "export", str(src), "-o", str(out), "--force"]) == 0
