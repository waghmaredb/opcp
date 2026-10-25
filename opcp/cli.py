"""Command-line interface: ``opcp scorecard``, ``opcp validate``, ``opcp conformance-demo``, ``opcp demo``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from ._io import ValidationFailed, errors, load_document, schema_validator
from ._paths import data_dir


def _scorecard_init(args: argparse.Namespace) -> int:
    from .scorecard import template

    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(template(), encoding="utf-8")
    print(f"Created {path}. Fill it in, then run:\n  opcp scorecard run {path} -o report.html")
    return 0


def _scorecard_run(args: argparse.Namespace) -> int:
    from .scorecard import evaluate_file, render_html, render_json, render_text

    try:
        result = evaluate_file(args.path)
    except ValidationFailed as exc:
        print(f"Could not read {args.path}.\n{exc}", file=sys.stderr)
        return 2
    print(render_text(result))
    if args.output:
        Path(args.output).write_text(render_html(result), encoding="utf-8")
        print(f"\nReport written to {args.output}")
    if args.json:
        Path(args.json).write_text(render_json(result), encoding="utf-8")
        print(f"JSON written to {args.json}")
    return 0


def _scorecard_example(args: argparse.Namespace) -> int:
    source = data_dir("examples") / "example-bank.yaml"
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Copied the hypothetical example to {args.path}")
    return 0


def _scorecard_export(args: argparse.Namespace) -> int:
    from .registers import export_file

    text = export_file(args.path, args.register)
    if not args.output:
        sys.stdout.write(text)
        return 0
    path = Path(args.output)
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(text, encoding="utf-8")
    print(f"Wrote suggested {args.register.upper()} register values to {path}.\n"
          "These are suggestions for review, not a filing: check each value against your own records,\n"
          "and fill in the contract reference and provider code columns. See docs/REGISTERS.md.")
    return 0


def _scorecard_form(args: argparse.Namespace) -> int:
    import json

    from .questionbank import Bank

    bank = Bank.load()
    template = (Path(__file__).parent / "form_template.html").read_text(encoding="utf-8")
    payload = json.dumps(bank.raw, ensure_ascii=False).replace("</", "<\\/")
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(template.replace("/*BANK_JSON*/", payload), encoding="utf-8")
    print(f"Created {path}. Open it in a browser, answer the questions, download the answers file, then run:\n"
          f"  opcp scorecard run <answers file> -o report.html")
    return 0


KINDS = {"contract": "capability", "route": "route", "assessment": "scorecard", "answers": "answers", "questions": "question-bank"}


def _validate(args: argparse.Namespace) -> int:
    failed = False
    for path in args.paths:
        problems = errors(schema_validator(KINDS[args.kind]), load_document(path))
        if problems:
            failed = True
            print(f"{path}: INVALID")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"{path}: valid {args.kind}")
    return 1 if failed else 0


def _demo(args: argparse.Namespace) -> int:
    from .demo import run

    run()
    return 0


def _conformance_demo(args: argparse.Namespace) -> int:
    from .conformance import check_adapter
    from .demo import build

    from .conformance import check_runtime

    plane = build()
    ok = True
    for adapter in plane.adapters.values():
        report = check_adapter(adapter, plane.contracts[adapter.profile.capability])
        print(report.render())
        ok &= report.passed
    runtime = check_runtime()
    print(runtime.render())
    return 0 if ok and runtime.passed else 1


def _shadow_report(args: argparse.Namespace) -> int:
    import json

    from .drill import load_jsonl, render_text, summarise

    summaries = summarise(load_jsonl(args.path))
    if args.json:
        print(json.dumps([s.to_dict() for s in summaries], indent=2))
    else:
        sys.stdout.write(render_text(summaries))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opcp", description="Open Process Control Plane tools. Everything runs locally.")
    parser.add_argument("--version", action="version", version=f"opcp {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sc = sub.add_parser("scorecard", help="Exit-Readiness Scorecard")
    scs = sc.add_subparsers(dest="action", required=True)
    p = scs.add_parser("init", help="Create a commented assessment template to fill in")
    p.add_argument("path", nargs="?", default="assessment.yaml")
    p.add_argument("--force", action="store_true", help="Overwrite an existing file")
    p.set_defaults(func=_scorecard_init)
    p = scs.add_parser("run", help="Rate an assessment and write a report")
    p.add_argument("path")
    p.add_argument("-o", "--output", help="Write a one-page HTML report to this path")
    p.add_argument("--json", help="Also write machine-readable results to this path")
    p.set_defaults(func=_scorecard_run)
    p = scs.add_parser("form", help="Create the offline assessment form (one HTML file)")
    p.add_argument("path", nargs="?", default="assessment-form.html")
    p.add_argument("--force", action="store_true", help="Overwrite an existing file")
    p.set_defaults(func=_scorecard_form)
    p = scs.add_parser("export", help="Suggest regulatory register values (EU DORA) from an assessment")
    p.add_argument("path")
    p.add_argument("--register", choices=["dora"], default="dora", help="Which register (only dora for now)")
    p.add_argument("-o", "--output", help="Write CSV to this path (default: print it)")
    p.add_argument("--force", action="store_true", help="Overwrite an existing file")
    p.set_defaults(func=_scorecard_export)
    p = scs.add_parser("example", help="Copy a filled-in hypothetical example")
    p.add_argument("path", nargs="?", default="example-assessment.yaml")
    p.add_argument("--force", action="store_true", help="Overwrite an existing file")
    p.set_defaults(func=_scorecard_example)

    p = sub.add_parser("validate", help="Validate contracts, routes or assessments against the schemas")
    p.add_argument("kind", choices=sorted(KINDS))
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=_validate)

    p = sub.add_parser("shadow-report", help="Summarise a shadow drill from an exported event log (JSON lines)")
    p.add_argument("path")
    p.add_argument("--json", action="store_true", help="Print machine-readable results")
    p.set_defaults(func=_shadow_report)

    p = sub.add_parser("demo", help="Run the reference runtime with simulated suppliers")
    p.set_defaults(func=_demo)
    p = sub.add_parser("conformance-demo", help="Run adapter and runtime conformance checks")
    p.set_defaults(func=_conformance_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    import yaml

    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"File not found: {exc.filename}", file=sys.stderr)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        print(f"The file is not valid YAML{where}. Check indentation and colons near that point.", file=sys.stderr)
    except ValidationFailed as exc:
        print(str(exc), file=sys.stderr)
    except ValueError as exc:  # e.g. a malformed date
        print(f"Could not read the file: {exc}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
