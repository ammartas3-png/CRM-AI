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
    print(json.dumps({"written_to": str(out), "summary": {
        "total": report.get("total_labeled"),
        "agree": report.get("agree"),
        "disagree": report.get("disagree"),
        "agree_rate": report.get("agree_rate"),
        "top_conflicts": report.get("top_conflicts", [])[:5],
    }}, ensure_ascii=False, indent=2))
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

    args = p.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
