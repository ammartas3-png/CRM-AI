from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "quality-layer"))

from cascade import cascade_comment  # noqa: E402
from semantic_bank import semantic_route  # noqa: E402
from structured_out import canonicalize_status, validate_ai_batch  # noqa: E402


def test_semantic_soft_money_routes_call_again():
    r = semantic_route("no money until salary then will start deposit")
    assert r["matched"] is True
    assert r["status"] == "Call Again"


def test_semantic_agent_dial_not_preferred_as_call_again():
    r = semantic_route("cb : vm")
    # Either unmatched or routed away from Call Again
    assert not (r.get("matched") and r.get("status") == "Call Again")


def test_structured_out_accepts_valid_batch():
    batch = [
        {
            "account no": "A1",
            "Validation Result": "Wrong",
            "Suggested Status": "Call Again",
            "Reason": "soft money with plan",
        }
    ]
    out = validate_ai_batch(batch, expected_count=1)
    assert out["ok"] is True
    assert out["normalized"][0]["Suggested Status"] == "Call Again"


def test_structured_out_rejects_bad_status():
    batch = [
        {
            "account no": "A1",
            "Validation Result": "Wrong",
            "Suggested Status": "Potential",
        }
    ]
    out = validate_ai_batch(batch)
    assert out["ok"] is False


def test_canonicalize_aliases():
    assert canonicalize_status("ca") == "Call Again"
    assert canonicalize_status("np") == "No Potential"


def test_cascade_includes_semantic_stage_key():
    result = cascade_comment("no money until salary then proceed", min_fuzzy=50.0)
    assert "semantic" in result
    assert "fuzzy" in result
