"""Great-Expectations-inspired run checkpoint for a classified lead batch."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _fold(s: str) -> str:
    return str(s or "").strip().lower()


def _pick(lead: dict[str, Any], *keys: str) -> str:
    for k in keys:
        if lead.get(k):
            return str(lead[k])
    return ""


def run_checkpoint(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Emit a GE-style expectation report over Validation Result / status distribution."""
    total = len(leads)
    vr_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    missing_comments = 0
    missing_account = 0
    correct = wrong = manual = other = 0

    for lead in leads:
        vr = _fold(_pick(lead, "Validation Result", "validation_result"))
        sug = _pick(lead, "Suggested Status", "suggested_status")
        comments = _pick(lead, "last 10 comments", "last_10_comments", "comments")
        acc = _pick(lead, "account no", "account_no")
        vr_counts[vr or "(empty)"] += 1
        if sug:
            status_counts[sug] += 1
        if not comments.strip():
            missing_comments += 1
        if not acc.strip():
            missing_account += 1
        if vr in {"correct", "true"}:
            correct += 1
        elif vr in {"wrong", "false"}:
            wrong += 1
        elif "manual" in vr:
            manual += 1
        else:
            other += 1

    expectations = [
        {
            "expectation": "expect_table_row_count_to_be_between",
            "kwargs": {"min_value": 1, "max_value": 100000},
            "success": 1 <= total <= 100000,
            "observed": total,
        },
        {
            "expectation": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "account no"},
            "success": missing_account == 0,
            "observed_nulls": missing_account,
        },
        {
            "expectation": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "last 10 comments"},
            "success": missing_comments == 0,
            "observed_nulls": missing_comments,
        },
        {
            "expectation": "expect_wrong_rate_below",
            "kwargs": {"max_wrong_rate": 0.35},
            "success": (wrong / total if total else 0) <= 0.35,
            "observed_wrong_rate": round(wrong / total, 4) if total else 0.0,
        },
        {
            "expectation": "expect_correct_bucket_present",
            "kwargs": {},
            "success": correct > 0 or total == 0,
            "observed_correct": correct,
        },
    ]
    success = all(e["success"] for e in expectations)
    return {
        "ok": success,
        "backend": "great-expectations-inspired",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "statistics": {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "manual": manual,
            "other": other,
            "validation_result_counts": dict(vr_counts),
            "suggested_status_top": status_counts.most_common(15),
            "missing_comments": missing_comments,
            "missing_account": missing_account,
        },
        "expectations": expectations,
        "success_percent": round(
            100.0 * sum(1 for e in expectations if e["success"]) / max(1, len(expectations)), 2
        ),
    }


def write_checkpoint(report: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
