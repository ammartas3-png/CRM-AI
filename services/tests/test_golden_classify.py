"""Golden-set regression tests for CRM classify rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "rule-engine"))

from crm_classify import classify_lead, status_canon  # noqa: E402

GOLDEN = ROOT / "evals" / "golden_leads.jsonl"


def load_golden():
    rows = []
    for line in GOLDEN.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def test_golden_leads():
    rows = load_golden()
    assert len(rows) >= 10
    failures = []
    for row in rows:
        lead = {
            "account no": row["account no"],
            "customer status": row["customer status"],
            "last 10 comments": row["last 10 comments"],
        }
        r = classify_lead(lead)
        if "expect_status" in row and r.suggested_status != row["expect_status"]:
            # allow family match if expect_status_family also set later
            if "expect_status_family" not in row:
                failures.append(f"{row['account no']}: status {r.suggested_status!r} != {row['expect_status']!r}")
        if "expect_status_family" in row:
            if status_canon(r.suggested_status) != row["expect_status_family"]:
                failures.append(
                    f"{row['account no']}: family {status_canon(r.suggested_status)!r} != {row['expect_status_family']!r}"
                )
        if "expect_validation" in row and r.validation_result != row["expect_validation"]:
            failures.append(
                f"{row['account no']}: validation {r.validation_result!r} != {row['expect_validation']!r}"
            )
        if "expect_source_contains" in row and row["expect_source_contains"].lower() not in r.decision_source.lower():
            failures.append(
                f"{row['account no']}: source {r.decision_source!r} missing {row['expect_source_contains']!r}"
            )
        if row.get("expect_skip_ai") is True and not r.skip_ai:
            failures.append(f"{row['account no']}: expected skipAI")
    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    test_golden_leads()
    print(f"golden-ok ({len(load_golden())} cases)")
