#!/usr/bin/env python3
"""Offline conflict report + Correct-bucket review enqueue helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "quality-layer"))

from conflicts import build_conflict_report, write_report  # noqa: E402
from review_queue import (  # noqa: E402
    enqueue_correct_sample,
    export_argilla_records,
    list_pending,
    maybe_push_argilla,
)


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
    src = Path(args.input)
    leads = []
    if src.suffix == ".jsonl":
        for line in src.read_text(encoding="utf-8").splitlines():
            if line.strip():
                leads.append(json.loads(line))
    else:
        leads = json.loads(src.read_text(encoding="utf-8"))
        if isinstance(leads, dict) and "leads" in leads:
            leads = leads["leads"]
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
        "6. Promote agreed flips into vault/rules + golden_leads.jsonl + Memory Match.",
    ]
    print("Correct-bucket HITL routine")
    print("==========================")
    for s in steps:
        print(s)
    if args.input:
        print("\n-- running enqueue-correct --")
        return cmd_enqueue(argparse.Namespace(input=args.input, limit=args.limit))
    return 0


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

    args = p.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
