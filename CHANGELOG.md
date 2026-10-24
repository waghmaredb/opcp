# Changelog

## 0.2.0 (draft) — 2026-10-24

A standard way to collect inputs, and the evidence behind the method.

- **Question bank** (`questions/exit-readiness.yaml`, version 0.2): 22 questions with stable IDs, anchored options, a named respondent role for each, evidence guidance, triage and five consistency checks.
- **Evidence levels**: every answer is Declared, Documented or Tested; reports show each measure's weakest evidence and the share of answers backed by a record or test.
- **Framework references**: 74 clause-level references to 15 regulations, guidelines and standards (DORA and its RTS, EU Data Act, EBA, APRA CPS 230, MAS, PRA, FSB, Basel Committee, IOSCO, NIST, CSA). Each source records how its text was checked; about 45 locators were spot-checked by a second reviewer. Optional filter by jurisdiction.
- **Research base** (`docs/EVIDENCE.md`, `docs/REFERENCES.md`): 20 verified sources, from peer-reviewed papers to supervisory analysis, explaining why each measure matters.
- **Offline form** (`opcp scorecard form`): one HTML file, no network, saves progress in the browser, exports an answers file.
- **Reports** now state they are a self-assessment, show sign-off and review, consistency flags, evidence and references.
- New question: whether the firm can terminate on a regulator's direction.

## 0.1.0 (draft) — 2026-10-24

First public draft for comment.

- Specification v0.1: capability archetypes, standard envelope, capability contracts, two-stage routing, authority gate, context lease, exit-readiness scorecard, conformance.
- JSON Schemas for capability contracts, routes, envelopes and scorecard assessments.
- Example catalogue: five capability contracts covering the Check, Extract, Notify, Transact and Human task archetypes.
- Exit-Readiness Scorecard: local command-line tool that turns an assessment file into a one-page HTML report.
- Reference runtime: minimal control plane with router, authority gate, context lease, event log and conformance runner, plus a runnable demo.
