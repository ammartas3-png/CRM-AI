"""Instructor / Outlines inspired structured status validation (no LLM required)."""

from __future__ import annotations

from typing import Any

ALLOWED_STATUSES: frozenset[str] = frozenset(
    {
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
)

STATUS_ALIASES: dict[str, str] = {
    "call again": "Call Again",
    "ca": "Call Again",
    "recall": "Recall",
    "no potential": "No Potential",
    "np": "No Potential",
    "no interest": "No Interest",
    "ni": "No Interest",
    "no answer": "No Answer 1-5",
    "no answer 1-5": "No Answer 1-5",
    "na": "No Answer 1-5",
    "no answer 5 up": "No Answer 5 UP",
    "no answer 5+": "No Answer 5 UP",
    "n5": "No Answer 5 UP",
    "no language": "No Language",
    "language barrier": "No Language",
    "denied registration": "Denied Registration",
    "wrong number or email": "Wrong Number or Email",
    "wrong number": "Wrong Number or Email",
    "under 18": "Under 18",
    "invalid country": "Invalid Country",
    "keep crm": "Keep CRM",
    "manual check": "Manual Check",
    "manual": "Manual Check",
    "decline": "Decline",
    "duplicate": "Duplicate",
    "dnc": "DNC",
}

VALID_RESULTS = frozenset({"Correct", "Wrong", "Manual Check"})


def canonicalize_status(raw: Any) -> str | None:
    s = str(raw or "").strip()
    if not s:
        return None
    if s in ALLOWED_STATUSES:
        return s
    return STATUS_ALIASES.get(s.lower())


def validate_ai_object(obj: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return {"ok": False, "index": index, "errors": ["not_an_object"], "normalized": None}

    account = obj.get("account no") or obj.get("account_no") or obj.get("id")
    vr = obj.get("Validation Result") or obj.get("validation_result")
    status_raw = (
        obj.get("Suggested Status")
        or obj.get("suggested_status")
        or obj.get("status")
    )
    status = canonicalize_status(status_raw)

    if account is None or str(account).strip() == "":
        errors.append("missing:account no")
    if vr is None or str(vr).strip() == "":
        errors.append("missing:Validation Result")
    elif str(vr).strip() not in VALID_RESULTS:
        errors.append(f"bad_validation_result:{vr}")
    if status is None:
        errors.append(f"bad_status:{status_raw}")

    normalized = None
    if not errors:
        normalized = {
            "account no": str(account).strip(),
            "Validation Result": str(vr).strip(),
            "Suggested Status": status,
            "Reason": str(obj.get("Reason") or obj.get("reason") or "")[:240],
            "Rule Trigger": str(obj.get("Rule Trigger") or ""),
            "Appointment Detected": str(obj.get("Appointment Detected") or "No"),
            "Appointment Status": str(obj.get("Appointment Status") or "No Appointment"),
            "Appointment Outcome": str(obj.get("Appointment Outcome") or ""),
            "Appointment Detail": str(obj.get("Appointment Detail") or ""),
        }
    return {"ok": not errors, "index": index, "errors": errors, "normalized": normalized}


def validate_ai_batch(items: list[Any], *, expected_count: int | None = None) -> dict[str, Any]:
    if not isinstance(items, list):
        return {
            "ok": False,
            "error": "batch_not_array",
            "valid": 0,
            "invalid": 0,
            "results": [],
            "inspired_by": "instructor+outlines structured output",
        }
    results = [
        validate_ai_object(x if isinstance(x, dict) else {"_raw": x}, index=i)
        for i, x in enumerate(items)
    ]
    valid = sum(1 for r in results if r["ok"])
    invalid = len(results) - valid
    count_ok = expected_count is None or len(items) == expected_count
    return {
        "ok": invalid == 0 and count_ok,
        "valid": valid,
        "invalid": invalid,
        "count": len(items),
        "expected_count": expected_count,
        "count_match": count_ok,
        "results": results,
        "normalized": [r["normalized"] for r in results if r.get("normalized")],
        "inspired_by": "instructor+outlines structured output",
    }


def validate_verifier_object(obj: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return {"ok": False, "index": index, "errors": ["not_an_object"]}
    if not str(obj.get("id") or "").strip():
        errors.append("missing:id")
    verdict = str(obj.get("verdict") or "").strip().lower()
    if verdict not in {"agree", "disagree"}:
        errors.append(f"bad_verdict:{verdict}")
    status = canonicalize_status(obj.get("correct_status") or obj.get("Suggested Status"))
    if status is None:
        errors.append(f"bad_correct_status:{obj.get('correct_status')}")
    return {
        "ok": not errors,
        "index": index,
        "errors": errors,
        "normalized": None
        if errors
        else {
            "id": str(obj.get("id")),
            "verdict": verdict,
            "correct_status": status,
            "sentence_ok": bool(obj.get("sentence_ok", verdict == "agree")),
            "matched_keyword": str(obj.get("matched_keyword") or "")[:120],
            "match_context": str(obj.get("match_context") or "")[:240],
            "reason": str(obj.get("reason") or "")[:120],
        },
    }


def validate_verifier_batch(items: list[Any]) -> dict[str, Any]:
    if not isinstance(items, list):
        return {"ok": False, "error": "batch_not_array", "results": []}
    results = [
        validate_verifier_object(x if isinstance(x, dict) else {}, index=i)
        for i, x in enumerate(items)
    ]
    valid = sum(1 for r in results if r["ok"])
    return {
        "ok": valid == len(results) and len(results) > 0,
        "valid": valid,
        "invalid": len(results) - valid,
        "results": results,
        "normalized": [r["normalized"] for r in results if r.get("normalized")],
        "inspired_by": "instructor+outlines structured output",
    }
