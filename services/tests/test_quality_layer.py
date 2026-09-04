import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
QL = ROOT / "services" / "quality-layer"
import sys

sys.path.insert(0, str(QL))

from conflicts import build_conflict_report  # noqa: E402
from router import detect_families, enrich_lead, route_comment  # noqa: E402


def test_soft_money_routes_to_call_again():
    r = route_comment(
        "dont have money will get my salary in few days then i can proceed",
        family="money",
    )
    assert r["matched"] is True
    assert r["status"] == "Call Again"


def test_language_family_detected():
    assert "language" in detect_families("pu no english hu")


def test_enrich_overrides_no_potential_when_soft_money():
    lead = enrich_lead(
        {
            "account no": "T1",
            "customer status": "Call Again",
            "Suggested Status": "No Potential",
            "Validation Result": "Wrong",
            "last 10 comments": "no money until salary then will start",
        }
    )
    assert lead["_quality_router_applied"] is True
    assert lead["Suggested Status"] == "Call Again"


def test_conflict_report_runs_on_evals():
    paths = [
        ROOT / "evals" / "golden_leads.jsonl",
        ROOT / "evals" / "wrong_review_cases.jsonl",
    ]
    report = build_conflict_report([p for p in paths if p.exists()])
    assert report["total_labeled"] >= 1
    assert "top_conflicts" in report
