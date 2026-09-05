#!/usr/bin/env python3
"""Sheet ↔ AI-prompt gantry auditor (stdlib only).

Inspired by Great Expectations / Evidently expectation checks.

  python3 scripts/sheet_prompt_audit.py
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "evals" / "rules_sheet.json"
WORKFLOW = ROOT / "n8n-import" / "05-V2-smart-upgraded.workflow.json"

ALLOWED = {
    "Call Again",
    "Recall",
    "No Potential",
    "No Interest",
    "No Answer 1-5",
    "No Answer 5 UP",
    "No Language",
    "Denied Registration",
    "Wrong Number or Email",
    "Under 18",
    "Invalid Country",
    "Keep CRM",
    "Manual Check",
    "Decline",
    "Duplicate",
    "DNC",
}

BARE_STATUS = {
    "call again",
    "recall",
    "no potential",
    "no interest",
    "no answer",
    "no answer 1-5",
    "wrong number",
    "under 18",
    "no language",
}

DIALER_SHORT = {"na", "vm", "rej", "db", "dvm", "ndt", "cnbr", "navm", "pu", "hu"}


def load_ai_prompt() -> str:
    wf = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    node = next(n for n in wf["nodes"] if n["name"] == "AI Agent")
    return node["parameters"]["options"]["systemMessage"]


def fold(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def audit_row(row: dict) -> list[dict]:
    issues: list[dict] = []
    rn = row.get("row_number")
    trig = str(row.get("trigger_phrase") or row.get("example_comment") or "").strip()
    status = str(row.get("suggested_status") or "").strip()
    active = bool(row.get("active", True))
    when = fold(str(row.get("when_to_use") or ""))
    when_not = fold(str(row.get("when_not_to_use") or ""))
    ft = fold(trig)

    if status and status not in ALLOWED:
        issues.append({"code": "unknown_status", "severity": "P0", "detail": status})

    if active and ft in BARE_STATUS:
        issues.append({"code": "bare_status_paste", "severity": "P0", "detail": trig})

    if active and ft in DIALER_SHORT:
        if "dialer" not in when and "no answer" not in fold(status):
            issues.append({"code": "too_short_dialer", "severity": "P0", "detail": trig})
        elif "alone" not in when_not and "wrong number" in fold(status):
            issues.append({"code": "dialer_misuse_wrong_number", "severity": "P1", "detail": trig})

    moneyish = bool(re.search(r"\b(no money|broke|cant afford|can't afford|no funds|no capital)\b", ft))
    plan = bool(re.search(r"\b(salary|funding|borrow|arrange|next week|tomorrow|deposit)\b", ft + " " + when))
    cb = bool(re.search(r"\b(call (me |him |her )?back|call again|cb\b|callback)\b", ft + " " + when))
    if active and moneyish and status == "Call Again" and not (plan or cb):
        issues.append({"code": "money_to_ca_without_plan", "severity": "P0", "detail": trig})
    if active and moneyish and status == "No Potential" and plan and cb and "hard" not in when:
        issues.append({"code": "soft_money_marked_np", "severity": "P1", "detail": trig})

    refusal = bool(re.search(r"\b(not interest|dont want|doesn't want|cancel|scam|leave it)\b", ft))
    if active and refusal and status == "Call Again":
        issues.append({"code": "refusal_to_ca", "severity": "P1", "detail": trig})

    return [
        {"row": rn, "trigger": trig, "status": status, "active": active, **iss}
        for iss in issues
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", default=str(ROOT / "evals" / "sheet_prompt_audit.json"))
    ap.add_argument("--fail-on-p0", action="store_true")
    args = ap.parse_args()

    rows = json.loads(SHEET.read_text(encoding="utf-8"))
    prompt = load_ai_prompt()
    findings: list[dict] = []
    for row in rows:
        findings.extend(audit_row(row))

    by_sev = Counter(f["severity"] for f in findings)
    by_code = Counter(f["code"] for f in findings)
    report = {
        "total_rows": len(rows),
        "issues": len(findings),
        "by_severity": dict(by_sev),
        "by_code": dict(by_code),
        "inactive_count": sum(1 for r in rows if not r.get("active", True)),
        "prompt_has_money_tree": bool(re.search(r"CANONICAL MONEY", prompt, re.I)),
        "findings": findings,
        "inspired_by": ["great_expectations", "evidently", "promptfoo"],
    }
    Path(args.write).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "written_to": args.write,
                "total_rows": report["total_rows"],
                "issues": report["issues"],
                "by_severity": report["by_severity"],
                "prompt_has_money_tree": report["prompt_has_money_tree"],
            },
            indent=2,
        )
    )
    if args.fail_on_p0 and by_sev.get("P0", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
