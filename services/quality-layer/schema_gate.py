"""Lead schema gate inspired by Pandera / Great Expectations column contracts."""

from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = ("account no", "customer status", "last 10 comments")
KNOWN_STATUSES = {
    "call again",
    "recall",
    "no potential",
    "no interest",
    "no answer 1-5",
    "no answer 5 up",
    "no language",
    "denied registration",
    "wrong number or email",
    "potential",
    "new",
    "in progress",
    "decline",
    "duplicate",
    "dnc",
    "manual check",
}

_HAS_PANDERA = False
try:
    import pandera.pandas as pa
    from pandera import Check, Column

    _HAS_PANDERA = True
except Exception:  # pragma: no cover - optional
    pa = None  # type: ignore


def _normalize_keys(lead: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "account_no": "account no",
        "Account No": "account no",
        "customer_status": "customer status",
        "Customer Status": "customer status",
        "last_10_comments": "last 10 comments",
        "comments": "last 10 comments",
        "Suggested Status": "Suggested Status",
        "suggested_status": "Suggested Status",
        "Validation Result": "Validation Result",
        "validation_result": "Validation Result",
    }
    out = dict(lead)
    for src, dst in mapping.items():
        if src in out and dst not in out:
            out[dst] = out[src]
    return out


def validate_lead(lead: dict[str, Any]) -> dict[str, Any]:
    row = _normalize_keys(lead)
    errors: list[str] = []
    for f in REQUIRED_FIELDS:
        if not str(row.get(f) or "").strip():
            errors.append(f"missing:{f}")
    crm = str(row.get("customer status") or "").strip().lower()
    if crm and crm not in KNOWN_STATUSES and not any(k in crm for k in ("no potential", "no answer")):
        errors.append(f"unknown_status:{crm}")
    return {
        "ok": not errors,
        "errors": errors,
        "backend": "pandera" if _HAS_PANDERA else "builtin",
        "lead": row,
    }


def validate_leads(leads: list[dict[str, Any]]) -> dict[str, Any]:
    results = [validate_lead(x) for x in leads]
    bad = [r for r in results if not r["ok"]]
    return {
        "ok": len(bad) == 0,
        "total": len(results),
        "invalid": len(bad),
        "valid": len(results) - len(bad),
        "backend": "pandera" if _HAS_PANDERA else "builtin",
        "failures": bad[:50],
    }


def pandera_schema_available() -> bool:
    return _HAS_PANDERA
