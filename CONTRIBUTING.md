# Contributing

Thank you for helping. OPCP is useful only if it reflects how real businesses work, so contributions from operations, risk, legal and procurement people are as valuable as code.

## Ways to contribute

- **Capability contracts.** Propose a new contract in [`catalogue/`](catalogue/) for a capability that at least two vendors can fulfil (the two-vendor rule, spec section 6.4).
- **Adapters.** Implement a contract for a vendor, an internal system or a human team, and show it passes the conformance suite.
- **Specification feedback.** Open an issue on anything unclear, unworkable or missing in [`spec/SPEC.md`](spec/SPEC.md).
- **Scorecard improvements.** Better questions, better report wording, mappings to regulations in other jurisdictions.

## Developer Certificate of Origin

Every commit must be signed off, certifying the [Developer Certificate of Origin 1.1](https://developercertificate.org/). Add the sign-off with:

```bash
git commit -s
```

This adds a line such as:

```
Signed-off-by: Your Name <you@example.com>
```

There is no contributor licence agreement. You keep the copyright in your contribution and license it under Apache 2.0, the same as the rest of the project. See [GOVERNANCE.md](GOVERNANCE.md) for why.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Ground rules

- **No invented facts.** Regulatory mappings, standard identifiers (such as APQC or BIAN references) and vendor capabilities must cite a source. Leave a field empty rather than guess.
- **Specification changes** stay open for at least 14 days before merging.
- **Keep data local.** The scorecard and runtime must never make network calls or send telemetry unless a user explicitly configures an adapter that does.
