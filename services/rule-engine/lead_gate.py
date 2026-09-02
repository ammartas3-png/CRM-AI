"""Light Pandera / schema gate before classify (zero-token)."""

from __future__ import annotations

from typing import Any

import pandas as pd

try:
    import pandera.pandas as pa
    from pandera.typing import Series

    class LeadFrame(pa.DataFrameModel):
        account_no: Series[str] = pa.Field(alias="account no")
        customer_status: Series[str] = pa.Field(alias="customer status", nullable=True)
        last_10_comments: Series[str] = pa.Field(alias="last 10 comments", nullable=True)

        class Config:
            coerce = True
            strict = False

    HAS_PANDERA = True
except Exception:  # pragma: no cover
    HAS_PANDERA = False
    LeadFrame = None  # type: ignore


REQUIRED = ("account no",)


def _norm_lead(lead: dict[str, Any]) -> dict[str, Any]:
    out = dict(lead)
    # common aliases
    if "account no" not in out and out.get("account_no"):
        out["account no"] = out["account_no"]
    if "customer status" not in out and out.get("customer_status"):
        out["customer status"] = out["customer_status"]
    if "last 10 comments" not in out:
        out["last 10 comments"] = out.get("comments") or out.get("last_10_comments") or ""
    return out


def gate_leads(leads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate / coerce leads. Returns (clean_leads, issues)."""
    issues: list[str] = []
    if not leads:
        return [], ["empty leads array"]

    normalized = [_norm_lead(x) for x in leads]
    for i, row in enumerate(normalized):
        for col in REQUIRED:
            if not str(row.get(col) or "").strip():
                issues.append(f"row {i}: missing {col}")

    if HAS_PANDERA and LeadFrame is not None:
        try:
            df = pd.DataFrame(normalized)
            # ensure required columns exist for pandera
            for col in ("account no", "customer status", "last 10 comments"):
                if col not in df.columns:
                    df[col] = ""
            LeadFrame.validate(df, lazy=True)
        except Exception as exc:  # pandera SchemaErrors or other
            msg = str(exc)
            if len(msg) > 500:
                msg = msg[:500] + "…"
            issues.append(f"pandera: {msg}")

    # Drop rows missing account no; keep others
    clean = [r for r in normalized if str(r.get("account no") or "").strip()]
    if not clean and normalized:
        issues.append("no rows with account no after gate")
    return clean, issues
