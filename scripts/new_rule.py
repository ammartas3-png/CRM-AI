#!/usr/bin/env python3
"""Scaffold a new CRM rule: vault note + golden stub + MEMORY index link."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "vault" / "rules"
MEMORY = ROOT / "vault" / "MEMORY.md"
GOLDEN = ROOT / "evals" / "golden_leads.jsonl"


def slug(s: str) -> str:
    x = s.strip().lower()
    x = re.sub(r"[^a-z0-9]+", "-", x).strip("-")
    return x or "new-rule"


def main() -> None:
    p = argparse.ArgumentParser(description="Create vault rule + golden stub")
    p.add_argument("--id", required=True, help="rule id / filename stem")
    p.add_argument("--title", required=True, help="human title")
    p.add_argument("--status", required=True, help="expected Suggested Status")
    p.add_argument("--crm", default="Call Again", help="sample CRM status")
    p.add_argument("--comments", default="2026-09-02 10:00 | X | na;", help="sample comments")
    p.add_argument("--validation", default="", help="optional expect_validation")
    p.add_argument("--note", default="", help="short note")
    args = p.parse_args()

    rid = slug(args.id)
    RULES.mkdir(parents=True, exist_ok=True)
    path = RULES / f"{rid}.md"
    if path.exists():
        raise SystemExit(f"already exists: {path}")

    body = f"""---
id: {rid}
token_cost: 0
---

# {args.title}

**Expected status:** {args.status}

## When

(Describe trigger comments / CRM conditions.)

## When not

(Describe exceptions.)

## Example

- CRM: `{args.crm}`
- Comments: `{args.comments}`
- Result: **{args.status}**
"""
    path.write_text(body, encoding="utf-8")

    # MEMORY index
    mem = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else "# CRM-AI Rule Index\n\n"
    link = f"- [`{rid}`](rules/{rid}.md)"
    if rid not in mem:
        if "## Status rules" in mem:
            mem = mem.replace("## Status rules", f"## Status rules\n{link}", 1)
        else:
            mem = mem.rstrip() + f"\n\n## Status rules\n{link}\n"
        MEMORY.write_text(mem, encoding="utf-8")

    row = {
        "account no": f"ACC_{rid.upper().replace('-', '_')[:24]}",
        "customer status": args.crm,
        "last 10 comments": args.comments,
        "expect_status": args.status,
        "note": args.note or args.title,
    }
    if args.validation:
        row["expect_validation"] = args.validation
        del row["expect_status"]

    with GOLDEN.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"created {path}")
    print(f"appended golden stub → {GOLDEN}")
    print("next:")
    print("  1) Edit vault note + golden expect_* fields")
    print("  2) Implement in services/rule-engine/crm_classify.py")
    print("  3) python3 scripts/validate_rule_system.py")
    print("  4) python3 -m pytest -q services/tests")
    print("  5) Sync live n8n Memory Match")


if __name__ == "__main__":
    main()
