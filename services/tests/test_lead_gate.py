"""Tests for Pandera / schema gate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rule-engine"))

from lead_gate import gate_leads  # noqa: E402
from crm_classify import classify_leads  # noqa: E402


def test_gate_requires_account():
    clean, issues = gate_leads([{"customer status": "Call Again", "last 10 comments": "na"}])
    assert clean == []
    assert any("account no" in x for x in issues)


def test_gate_accepts_alias():
    clean, issues = gate_leads(
        [{"account_no": "A1", "customer_status": "New", "comments": "hello"}]
    )
    assert len(clean) == 1
    assert clean[0]["account no"] == "A1"
    assert "last 10 comments" in clean[0]


def test_classify_with_gate_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("CLASSIFY_CACHE_PATH", str(tmp_path / "c.sqlite"))
    leads = [
        {
            "account no": "G1",
            "customer status": "Potential",
            "last 10 comments": "2026-09-01 10:00 | X | interested;",
        }
    ]
    r1 = classify_leads(leads, use_cache=True, gate=True)
    assert r1["ok"] and r1["total"] == 1
    assert r1["leads"][0]["skipAI"] is True
    r2 = classify_leads(leads, use_cache=True, gate=True)
    assert r2["cache_hits"] >= 1


if __name__ == "__main__":
    test_gate_requires_account()
    test_gate_accepts_alias()
    import os, tempfile
    from pathlib import Path as P
    td = tempfile.mkdtemp()
    os.environ["CLASSIFY_CACHE_PATH"] = str(P(td) / "c.sqlite")
    leads = [
        {
            "account no": "G1",
            "customer status": "Potential",
            "last 10 comments": "2026-09-01 10:00 | X | interested;",
        }
    ]
    r1 = classify_leads(leads, use_cache=True, gate=True)
    r2 = classify_leads(leads, use_cache=True, gate=True)
    assert r1["ok"] and r2["cache_hits"] >= 1
    print("lead-gate-ok")
