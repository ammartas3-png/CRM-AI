"""Tests for approved CRM business rules in rule-engine."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rule-engine"))

from crm_classify import classify_lead  # noqa: E402


def lead(acc: str, crm: str, comments: str) -> dict:
    return {
        "account no": acc,
        "customer status": crm,
        "last 10 comments": comments,
        "brand": "Riverquode",
        "Agent": "Test",
    }


def test_currently_busy_is_na():
    r = classify_lead(
        lead(
            "A1",
            "No Answer 1-5",
            "2026-09-02 10:00 | X | currently busy;\n2026-09-02 09:00 | X | na;",
        )
    )
    assert r.suggested_status == "No Answer 1-5"
    assert "currently_busy" in r.decision_source
    assert r.skip_ai is True


def test_invalid_mail_does_not_deny():
    r = classify_lead(
        lead(
            "A2",
            "No Answer 1-5",
            "2026-09-02 10:00 | X | na vm;\n2026-09-01 10:00 | X | invalid mail;",
        )
    )
    assert r.suggested_status.startswith("No Answer")
    assert "invalid_mail_ignored" in r.decision_source


def test_first_wrong_number_is_denied():
    r = classify_lead(
        lead(
            "A3",
            "Wrong Number or Email",
            "2026-09-02 10:00 | X | client said wrong number;",
        )
    )
    assert r.suggested_status == "Denied Registration"


def test_call_again_kept_under_5_na_days():
    r = classify_lead(
        lead(
            "A4",
            "Call Again",
            "2026-09-02 15:15 | X | v2 - rej;\n2026-09-02 15:13 | X | na;",
        )
    )
    assert r.suggested_status == "Call Again"
    assert "kept_under_5na" in r.decision_source


def test_call_again_wiped_after_5_days():
    comments = "\n".join(
        [
            "2026-09-06 10:00 | A | na;",
            "2026-09-05 10:00 | A | navm;",
            "2026-09-04 10:00 | A | rej;",
            "2026-09-03 10:00 | A | dnd;",
            "2026-09-02 10:00 | A | na;",
            "2026-09-01 12:00 | A | pu - asked for a cb later - hu;",
        ]
    )
    r = classify_lead(lead("A5", "Call Again", comments))
    assert r.suggested_status == "No Answer 5 UP"


def test_money_plus_callback_is_call_again():
    r = classify_lead(
        lead(
            "A6",
            "Call Again",
            "2026-09-01 14:11 | B | pu intro no money will receive salary tmrw cb tmrw 12 UAE time hu;",
        )
    )
    assert r.suggested_status == "Call Again"
    assert "money_plus_callback" in r.decision_source or "keep" in r.decision_source or "busy_after" in r.decision_source or "callback" in r.decision_source.lower() or r.skip_ai


def test_potential_manual_check():
    r = classify_lead(lead("A7", "Potential", "2026-09-01 10:00 | X | pu intro interested maybe;"))
    assert r.validation_result == "Manual Check"
    assert "Potential" in r.decision_source


def test_decline_manual_check():
    r = classify_lead(lead("A8", "Decline", "2026-09-01 10:00 | X | cb tmrw please;"))
    assert r.validation_result == "Manual Check"
    assert r.suggested_status == "Decline"


def test_recall_plus_callback_becomes_call_again():
    r = classify_lead(
        lead(
            "A9",
            "Recall",
            "2026-09-02 10:00 | X | he asked to call after 4 pm;",
        )
    )
    assert r.suggested_status == "Call Again"


if __name__ == "__main__":
    test_currently_busy_is_na()
    test_invalid_mail_does_not_deny()
    test_first_wrong_number_is_denied()
    test_call_again_kept_under_5_na_days()
    test_call_again_wiped_after_5_days()
    test_money_plus_callback_is_call_again()
    test_potential_manual_check()
    test_decline_manual_check()
    test_recall_plus_callback_becomes_call_again()
    print("crm-classify-ok")
