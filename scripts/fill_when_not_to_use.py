#!/usr/bin/env python3
"""Conflict I — fill empty/weak when_not_to_use on rules_sheet.json with tagged avoid text.

Tags are machine-readable by Memory Match (`[skip:…]`) and human-readable in Google Sheets.

  python3 scripts/fill_when_not_to_use.py          # write evals/rules_sheet.json
  python3 scripts/fill_when_not_to_use.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "evals" / "rules_sheet.json"

# Machine tags Memory Match honors via sheetAvoidBlocks()
TEMPLATES = {
    "call_again": (
        "[skip:negation][skip:agent_cb][skip:hard_money_dead][skip:next_month_as_ca] "
        "Do not fire if trigger is negated; agent-only cb:vm/cb na/call again rej; "
        "next month or hard/distant money without near plan → No Potential (not Call Again)."
    ),
    "no_potential_money": (
        "[skip:soft_money_plan] Near-term salary/arrange/friends OR concrete customer callback "
        "→ Call Again. Soft temporary open with no plan → Recall."
    ),
    "recall_refusal": (
        "[skip:negation] First refusal day → Recall; second distinct day → No Interest. "
        "Genuine newest customer callback after a stale refusal may reopen Call Again."
    ),
    "no_language": (
        "[skip:identity_denial] If customer denies being the registered person "
        "('im not X', 'wrong person', 'not me') → Denied Registration (identity > language)."
    ),
    "denied": (
        "[skip:language_only][skip:bare_didnt_register] Language barrier alone → No Language. "
        "Bare 'didnt register' without identity denial → Recall. no id/docs/bank → No Potential - no documents."
    ),
    "wrong_number": (
        "[skip:phone_alive] Newest dialer ring/NA/VM/DVM/unreachable → keep No Answer. "
        "Bare 'Invalid email - CRM' alone is not enough when phone is alive."
    ),
    "no_answer": (
        "[skip:agent_cb] Do not upgrade to Call Again from agent redial notes alone "
        "(cb:vm, cb na, call again rej)."
    ),
    "no_interest": (
        "[skip:negation] Requires clear refusal; first day usually Recall unless curse+istemiyorum. "
        "Do not fire on negated interest phrases alone without day logic."
    ),
    "generic": (
        "[skip:negation] Do not fire when the trigger phrase is negated or used in a false sense "
        "in the full sentence."
    ),
}

GENERIC_WEAK = re.compile(
    r"^if customer clearly refuses or cannot proceed structurally\.?$",
    re.I,
)


def pick_template(row: dict) -> str:
    status = str(row.get("suggested_status") or "").strip().lower()
    group = str(row.get("keyword_group") or "").strip().lower()
    trigger = str(row.get("trigger_phrase") or "").strip().lower()
    blob = f"{status} {group} {trigger}"

    if "no language" in status or group == "language":
        return TEMPLATES["no_language"]
    if "denied" in status or group == "denied":
        return TEMPLATES["denied"]
    if "wrong number" in status or "wrong email" in status:
        return TEMPLATES["wrong_number"]
    if "no answer" in status or group == "no_answer":
        return TEMPLATES["no_answer"]
    if "no interest" in status:
        return TEMPLATES["no_interest"]
    if "no potential" in status or group in ("payment", "finance", "money"):
        if any(k in blob for k in ("money", "fund", "afford", "capital", "broke", "salary", "payment")):
            return TEMPLATES["no_potential_money"]
        return TEMPLATES["no_potential_money"]
    if "recall" in status or group in ("rejection", "refusal"):
        return TEMPLATES["recall_refusal"]
    if "call again" in status or group in ("follow_up", "appointment", "positive"):
        return TEMPLATES["call_again"]
    return TEMPLATES["generic"]


def needs_fill(row: dict) -> bool:
    w = str(row.get("when_not_to_use") or "").strip()
    if not w:
        return True
    # Upgrade weak generic CA avoids that lack machine tags
    if GENERIC_WEAK.match(w) and "[skip:" not in w:
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = json.loads(SHEET.read_text())
    changed = []
    for r in rows:
        if not needs_fill(r):
            continue
        old = str(r.get("when_not_to_use") or "").strip()
        new = pick_template(r)
        # Keep prior prose if upgrading weak generic — prepend tags only when already specific?
        if old and GENERIC_WEAK.match(old):
            new = pick_template(r)
        r["when_not_to_use"] = new
        if not str(r.get("correction_source") or "").strip():
            r["correction_source"] = "conflict_i_when_not_to_use_2026-09-07"
        elif "conflict_i_when_not_to_use" not in str(r.get("correction_source")):
            r["correction_source"] = str(r["correction_source"]) + "|conflict_i_when_not_to_use_2026-09-07"
        changed.append((r.get("row_number"), r.get("trigger_phrase"), r.get("suggested_status"), old[:40], new[:60]))

    # Second pass: ensure critical families already having prose also carry [skip:] tags
    tag_added = 0
    for r in rows:
        w = str(r.get("when_not_to_use") or "")
        status = str(r.get("suggested_status") or "").lower()
        add: list[str] = []
        have = {t.lower() for t in re.findall(r"\[skip:[a-z0-9_]+\]", w, re.I)}
        if "call again" in status:
            for t in ("[skip:negation]", "[skip:agent_cb]", "[skip:hard_money_dead]", "[skip:next_month_as_ca]"):
                if t not in have:
                    add.append(t)
        if "no potential" in status and "[skip:soft_money_plan]" not in have:
            add.append("[skip:soft_money_plan]")
        if "no language" in status and "[skip:identity_denial]" not in have:
            add.append("[skip:identity_denial]")
        if "denied" in status:
            for t in ("[skip:language_only]", "[skip:bare_didnt_register]"):
                if t not in have:
                    add.append(t)
        if ("wrong number" in status or "wrong email" in status) and "[skip:phone_alive]" not in have:
            add.append("[skip:phone_alive]")
        if "no answer" in status and "[skip:agent_cb]" not in have:
            add.append("[skip:agent_cb]")
        if add:
            r["when_not_to_use"] = ("".join(add) + " " + w).strip()
            tag_added += 1

    empty_left = sum(1 for r in rows if not str(r.get("when_not_to_use") or "").strip())
    tagged = sum(1 for r in rows if "[skip:" in str(r.get("when_not_to_use") or ""))
    print(f"changed={len(changed)} tag_backfill={tag_added} empty_left={empty_left} tagged={tagged}/{len(rows)}")
    for row in changed[:12]:
        print(" ", row[0], row[1], "=>", row[2])
    if len(changed) > 12:
        print(f"  ... +{len(changed)-12} more")

    if not args.dry_run:
        SHEET.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {SHEET}")


if __name__ == "__main__":
    main()
