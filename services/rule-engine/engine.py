import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


COLUMN_ALIASES = {
    "name": {"name", "ad", "isim", "customer_name", "müşteri", "musteri"},
    "phone": {"phone", "telefon", "tel", "mobile", "gsm", "cep"},
    "email": {"email", "mail", "e-mail", "eposta", "e_posta"},
}


@dataclass
class ValidationResult:
    valid: bool
    message: str
    fixed_rows: int
    issues: list[str] = field(default_factory=list)
    ai_needed_rows: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    corrected_csv: str = ""
    corrected_filename: str = "corrected.csv"


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def canonicalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    mapping: dict[str, str] = {}
    issues: list[str] = []
    used_targets: set[str] = set()

    for col in df.columns:
        normalized = _normalize_header(col)
        matched = None
        for target, aliases in COLUMN_ALIASES.items():
            if normalized in aliases and target not in used_targets:
                matched = target
                break
        if matched:
            mapping[col] = matched
            used_targets.add(matched)

    out = df.rename(columns=mapping)
    for required in ("name", "phone", "email"):
        if required not in out.columns:
            issues.append(f"Missing required column: {required}")
            out[required] = ""
    return out, issues


def normalize_phone(value: Any) -> tuple[str, str | None]:
    raw = str(value or "").strip()
    if not raw:
        return "", "EMPTY_PHONE"

    cleaned = raw.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if cleaned.startswith("0") and len(re.sub(r"\D", "", cleaned)) == 11:
        cleaned = "+90" + cleaned[1:]

    digits = re.sub(r"\D", "", cleaned)
    if cleaned.startswith("+"):
        normalized = "+" + digits
    else:
        normalized = digits

    if len(digits) < 10:
        return normalized, "INVALID_PHONE"
    return normalized, None


def normalize_email(value: Any) -> tuple[str, str | None]:
    raw = str(value or "").strip().lower()
    if not raw:
        return "", "EMPTY_EMAIL"
    if "@" not in raw or "." not in raw.split("@")[-1]:
        return raw, "INVALID_EMAIL"
    return raw, None


def dataframe_from_upload(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    lower = (file_name or "").lower()
    if lower.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))
    raise ValueError("Unsupported file type. Use .xlsx, .xls, or .csv")


def run_zero_token_validation(
    file_name: str,
    file_bytes: bytes,
) -> ValidationResult:
    df = dataframe_from_upload(file_name, file_bytes)
    df = df.dropna(how="all")
    df, issues = canonicalize_columns(df)

    # Keep only working columns + originals extras
    core_cols = ["name", "phone", "email"]
    extra_cols = [c for c in df.columns if c not in core_cols]
    ordered_cols = core_cols + extra_cols
    df = df[ordered_cols].copy()

    for col in core_cols:
        df[col] = df[col].astype(str).replace({"nan": ""}).map(lambda x: str(x).strip())

    flags: list[str] = []
    fixed_rows = 0
    ai_needed: list[dict[str, Any]] = []

    phones: list[str] = []
    emails: list[str] = []
    row_flags: list[str] = []

    for idx, row in df.iterrows():
        phone, phone_issue = normalize_phone(row.get("phone", ""))
        email, email_issue = normalize_email(row.get("email", ""))
        name = str(row.get("name", "")).strip()

        changed = phone != str(row.get("phone", "")) or email != str(row.get("email", ""))
        if changed:
            fixed_rows += 1

        phones.append(phone)
        emails.append(email)

        local_flags = []
        if not name:
            local_flags.append("EMPTY_NAME")
        if phone_issue:
            local_flags.append(phone_issue)
        if email_issue:
            local_flags.append(email_issue)

        # Ambiguous rows that may need AI later (free-text name cleanup etc.)
        if name and len(name.split()) == 1 and not phone_issue and not email_issue:
            # single-token names are often incomplete; mark soft AI candidate
            local_flags.append("MAYBE_INCOMPLETE_NAME")

        flag_text = "|".join(local_flags)
        row_flags.append(flag_text)
        if local_flags:
            flags.extend(local_flags)
            if any(f.startswith("INVALID_") or f.startswith("EMPTY_") for f in local_flags):
                ai_needed.append(
                    {
                        "row_index": int(idx) if isinstance(idx, int) else idx,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "flags": local_flags,
                    }
                )

    df["phone"] = phones
    df["email"] = emails
    df["validation_flags"] = row_flags

    # Duplicate phones (zero token)
    seen: dict[str, int] = {}
    duplicate_count = 0
    for i, phone in enumerate(phones):
        if not phone:
            continue
        if phone in seen:
            duplicate_count += 1
            current = df.iloc[i]["validation_flags"]
            df.iat[i, df.columns.get_loc("validation_flags")] = (
                f"{current}|DUPLICATE_PHONE" if current else "DUPLICATE_PHONE"
            )
            issues.append(f"Duplicate phone at row {i + 1}: {phone}")
        else:
            seen[phone] = i

    # Hard AI only for unresolved invalid/empty fields (not soft maybe flags)
    hard_ai = [
        row
        for row in ai_needed
        if any(f.startswith("INVALID_") or f.startswith("EMPTY_") for f in row["flags"])
    ]

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    corrected_csv = csv_buffer.getvalue()

    unique_issues = sorted(set(issues + flags))
    valid = len(hard_ai) == 0 and duplicate_count == 0 and not any(
        i.startswith("Missing required column") for i in issues
    )

    if valid:
        message = (
            "Zero-token validation completed.\n"
            f"Rows fixed automatically: {fixed_rows}\n"
            f"AI needed: 0\n"
            "Corrected CSV ready."
        )
    else:
        message = (
            "Zero-token validation finished with remaining issues.\n"
            f"Rows fixed automatically: {fixed_rows}\n"
            f"Rows needing AI/manual review: {len(hard_ai)}\n"
            f"Issues: {', '.join(unique_issues[:12])}"
        )

    base = Path(file_name).stem if file_name else "database"
    return ValidationResult(
        valid=valid,
        message=message,
        fixed_rows=fixed_rows,
        issues=unique_issues,
        ai_needed_rows=hard_ai[:200],
        stats={
            "total_rows": int(len(df)),
            "fixed_rows": fixed_rows,
            "duplicate_phones": duplicate_count,
            "ai_needed_count": len(hard_ai),
            "token_cost": 0,
        },
        corrected_csv=corrected_csv,
        corrected_filename=f"{base}_corrected.csv",
    )


def write_run_note(vault_runs_dir: Path, result: ValidationResult, source_name: str) -> Path:
    vault_runs_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = vault_runs_dir / f"run-{stamp}.md"
    content = f"""---
type: run
source: {source_name}
valid: {str(result.valid).lower()}
token_cost: 0
fixed_rows: {result.fixed_rows}
ai_needed: {result.stats.get('ai_needed_count', 0)}
---

# Validation Run {stamp}

## Summary

{result.message}

## Stats

```json
{result.stats}
```

## Linked rules

- [[required-columns]]
- [[phone-normalize]]
- [[email-normalize]]
- [[duplicate-phone]]
"""
    path.write_text(content, encoding="utf-8")
    return path
