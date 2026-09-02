#!/usr/bin/env python3
"""Validate rule-management system: vault frontmatter + golden JSONL + index links."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "vault" / "rules"
MEMORY = ROOT / "vault" / "MEMORY.md"
GOLDEN = ROOT / "evals" / "golden_leads.jsonl"

REQUIRED_APPROVED = [
    "currently-busy-is-na",
    "invalid-mail-ignored",
    "call-again-5-na-days",
    "money-plus-callback",
    "potential-manual-check",
    "denied-registration-1x",
    "decline-manual-check",
    "recall-to-call-again",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def main() -> int:
    errors: list[str] = []

    if not RULES.is_dir():
        errors.append(f"missing {RULES}")
    else:
        md_files = sorted(RULES.glob("*.md"))
        if len(md_files) < 8:
            errors.append(f"expected >=8 rule files, found {len(md_files)}")
        ids = set()
        for path in md_files:
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            if not meta.get("id"):
                errors.append(f"{path.name}: missing frontmatter id")
            else:
                ids.add(meta["id"])
            if meta.get("token_cost") not in {"0", 0, "0"} and "token_cost" in meta:
                if str(meta.get("token_cost")) != "0":
                    errors.append(f"{path.name}: token_cost should be 0 for status rules")
            if len(text.strip()) < 40:
                errors.append(f"{path.name}: body too short")
        for rid in REQUIRED_APPROVED:
            if rid not in ids and not (RULES / f"{rid}.md").exists():
                errors.append(f"missing approved rule file: {rid}.md")

    if not GOLDEN.exists():
        errors.append(f"missing {GOLDEN}")
    else:
        rows = []
        for i, line in enumerate(GOLDEN.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"golden L{i}: {exc}")
                continue
            if "account no" not in row or "last 10 comments" not in row:
                errors.append(f"golden L{i}: need account no + last 10 comments")
            if not any(k.startswith("expect_") for k in row):
                errors.append(f"golden L{i}: need at least one expect_* field")
            rows.append(row)
        if len(rows) < 10:
            errors.append(f"golden set too small: {len(rows)}")

    if MEMORY.exists():
        mem = MEMORY.read_text(encoding="utf-8")
        for rid in REQUIRED_APPROVED:
            if rid not in mem:
                errors.append(f"MEMORY.md missing link/mention: {rid}")
    else:
        errors.append("missing vault/MEMORY.md")

    # docs entrypoint
    if not (ROOT / "docs" / "RULE-CHANGE.md").exists():
        errors.append("missing docs/RULE-CHANGE.md")

    if errors:
        print("validate_rule_system: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"validate_rule_system: OK ({len(list(RULES.glob('*.md')))} rules, golden ok)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
