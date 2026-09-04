#!/usr/bin/env python3
"""Offline conflict report + Correct-bucket review enqueue helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "quality-layer"))

from cascade import cascade_comment  # noqa: E402
from conflicts import build_conflict_report, write_report  # noqa: E402
from noise_strip import strip_noise  # noqa: E402
from review_queue import (  # noqa: E402
    enqueue_correct_sample,
    export_argilla_records,
    list_pending,
    maybe_push_argilla,
)
from run_checkpoint import run_checkpoint, write_checkpoint  # noqa: E402
from schema_gate import validate_leads  # noqa: E402


def _load_leads(path: Path) -> list:
    if path.suffix == ".jsonl":
        leads = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                leads.append(json.loads(line))
        return leads
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "leads" in data:
        return list(data["leads"])
    if isinstance(data, list):
        return data
    return [data]


def cmd_conflicts(_: argparse.Namespace) -> int:
    paths = [
        ROOT / "evals" / "golden_leads.jsonl",
        ROOT / "evals" / "wrong_review_cases.jsonl",
    ]
    report = build_conflict_report([p for p in paths if p.exists()])
    out = ROOT / "evals" / "conflict_report.json"
    write_report(report, out)
    print(
        json.dumps(
            {
                "written_to": str(out),
                "summary": {
                    "total": report.get("total_labeled"),
                    "agree": report.get("agree"),
                    "disagree": report.get("disagree"),
                    "agree_rate": report.get("agree_rate"),
                    "top_conflicts": report.get("top_conflicts", [])[:5],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    leads = _load_leads(Path(args.input))
    result = enqueue_correct_sample(leads, limit=args.limit)
    records = export_argilla_records(limit=args.limit)
    result["argilla"] = maybe_push_argilla(records)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_pending(args: argparse.Namespace) -> int:
    print(json.dumps({"items": list_pending(limit=args.limit)}, ensure_ascii=False, indent=2))
    return 0


def cmd_hitl_routine(args: argparse.Namespace) -> int:
    """Print + optionally run the Correct-bucket HITL routine after a big Excel run."""
    steps = [
        "1. Export validated leads JSON/JSONL from the Telegram run (or report pipeline).",
        "2. Sample Correct rows: python3 scripts/quality_tools.py enqueue-correct --input <file> --limit 30",
        "3. Review pending: python3 scripts/quality_tools.py pending --limit 30",
        "4. Record verdicts via POST /quality/review/verdict (or Argilla UI if configured).",
        "5. Rebuild conflict matrix: python3 scripts/quality_tools.py conflicts",
        "6. Run checkpoint: python3 scripts/quality_tools.py checkpoint --input <file>",
        "7. Promote agreed flips into vault/rules + golden_leads.jsonl + Memory Match.",
    ]
    print("Correct-bucket HITL routine")
    print("==========================")
    for s in steps:
        print(s)
    if args.input:
        print("\n-- running enqueue-correct --")
        return cmd_enqueue(argparse.Namespace(input=args.input, limit=args.limit))
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    leads = _load_leads(Path(args.input))
    report = run_checkpoint(leads)
    out = Path(args.output) if args.output else ROOT / "evals" / "run_checkpoint.json"
    write_checkpoint(report, out)
    print(json.dumps({"written_to": str(out), "ok": report.get("ok"), "statistics": report.get("statistics")}, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


def cmd_strip(args: argparse.Namespace) -> int:
    print(json.dumps(strip_noise(args.text, use_spacy=not args.no_spacy), ensure_ascii=False, indent=2))
    return 0


def cmd_cascade(args: argparse.Namespace) -> int:
    print(json.dumps(cascade_comment(args.text), ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    leads = _load_leads(Path(args.input))
    result = validate_leads(leads)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def main() -> int:
    p = argparse.ArgumentParser(description="CRM quality tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("conflicts", help="Build engine↔human conflict matrix")
    c.set_defaults(func=cmd_conflicts)

    e = sub.add_parser("enqueue-correct", help="Enqueue Correct-bucket sample for review")
    e.add_argument("--input", required=True, help="JSON/JSONL leads export")
    e.add_argument("--limit", type=int, default=50)
    e.set_defaults(func=cmd_enqueue)

    pend = sub.add_parser("pending", help="List pending review items")
    pend.add_argument("--limit", type=int, default=20)
    pend.set_defaults(func=cmd_pending)

    h = sub.add_parser("hitl-routine", help="Print Correct-bucket HITL checklist (optionally enqueue)")
    h.add_argument("--input", help="Optional leads JSON/JSONL to enqueue now")
    h.add_argument("--limit", type=int, default=30)
    h.set_defaults(func=cmd_hitl_routine)

    cp = sub.add_parser("checkpoint", help="GE-style run checkpoint over leads export")
    cp.add_argument("--input", required=True, help="JSON/JSONL leads export")
    cp.add_argument("--output", help="Optional output JSON path")
    cp.set_defaults(func=cmd_checkpoint)

    st = sub.add_parser("strip-noise", help="Strip agent-dial / bare-status noise from a comment")
    st.add_argument("--text", required=True)
    st.add_argument("--no-spacy", action="store_true")
    st.set_defaults(func=cmd_strip)

    ca = sub.add_parser("cascade", help="Run rules→fuzzy→ML cascade on one comment")
    ca.add_argument("--text", required=True)
    ca.set_defaults(func=cmd_cascade)

    v = sub.add_parser("validate", help="Schema-gate validate a leads export")
    v.add_argument("--input", required=True)
    v.set_defaults(func=cmd_validate)

    args = p.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
