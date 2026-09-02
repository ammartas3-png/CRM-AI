"""
Pandera schemas + Instructor-style structured validation helpers.
Used by local/self-hosted smart layer; n8n cloud uses JS equivalents.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

import pandas as pd

try:
    import pandera.pandas as pa
    from pandera.typing import Series
except Exception:  # pragma: no cover
    pa = None  # type: ignore


if pa is not None:
    class LeadSchema(pa.DataFrameModel):
        brand: Optional[Series[str]] = pa.Field(nullable=True)
        account_no: Series[str] = pa.Field(alias="account no")
        last_10_comments: Optional[Series[str]] = pa.Field(alias="last 10 comments", nullable=True)
        customer_status: Optional[Series[str]] = pa.Field(alias="customer status", nullable=True)
        country: Optional[Series[str]] = pa.Field(nullable=True)
        Agent: Optional[Series[str]] = pa.Field(nullable=True)

        class Config:
            coerce = True
            strict = False


def validate_leads_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    issues: list[str] = []
    if df.empty:
        return df, ["empty dataframe"]
    required = ["account no"]
    for col in required:
        if col not in df.columns:
            issues.append(f"missing column: {col}")
    if pa is None or "account no" not in df.columns:
        return df, issues
    try:
        clean = LeadSchema.validate(df, lazy=True)
        return clean, issues
    except Exception as exc:  # pandera schema errors
        issues.append(str(exc)[:400])
        return df, issues


# Instructor-compatible pydantic models (optional dependency)
try:
    from pydantic import BaseModel, Field

    class LeadClassification(BaseModel):
        account_no: str = Field(alias="account no")
        validation_result: Literal["Correct", "Wrong", "Manual Check"] = Field(
            alias="Validation Result"
        )
        suggested_status: str = Field(alias="Suggested Status")
        reason: str = Field(default="", alias="Reason")

        model_config = {"populate_by_name": True}

    class LeadClassificationBatch(BaseModel):
        results: list[LeadClassification]

except Exception:  # pragma: no cover
    LeadClassification = None  # type: ignore
    LeadClassificationBatch = None  # type: ignore


def parse_classification_payload(payload: Any) -> list[dict[str, Any]]:
    """Best-effort structured parse without requiring instructor at runtime."""
    if payload is None:
        return []
    if isinstance(payload, str):
        import json, re
        try:
            payload = json.loads(payload)
        except Exception:
            m = re.search(r"\[[\s\S]*\]", payload)
            payload = json.loads(m.group(0)) if m else []
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        return []
    out = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        out.append(row)
    return out
