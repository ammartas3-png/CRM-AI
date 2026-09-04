from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QL = ROOT / "services" / "quality-layer"
import sys

sys.path.insert(0, str(QL))

from cascade import cascade_comment, cascade_enrich_lead  # noqa: E402
from conflicts import build_conflict_report  # noqa: E402
from noise_strip import strip_noise  # noqa: E402
from router import detect_families, enrich_lead, route_comment  # noqa: E402
from run_checkpoint import run_checkpoint  # noqa: E402
from schema_gate import validate_lead, validate_leads  # noqa: E402
from setfit_router import predict_status  # noqa: E402


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


def test_noise_strip_removes_agent_dial():
    out = strip_noise("cb : vm | customer said no money until friday", use_spacy=False)
    assert "cb : vm" not in out["cleaned"].lower()
    assert "no money" in out["cleaned"].lower()
    assert out["backend"] == "flashtext-style"


def test_schema_gate_requires_fields():
    bad = validate_lead({"account no": "", "customer status": "Call Again"})
    assert bad["ok"] is False
    assert any(e.startswith("missing:") for e in bad["errors"])
    good = validate_leads(
        [
            {
                "account no": "A1",
                "customer status": "Call Again",
                "last 10 comments": "will call later",
            }
        ]
    )
    assert good["ok"] is True
    assert good["valid"] == 1


def test_checkpoint_on_sample_batch():
    report = run_checkpoint(
        [
            {
                "account no": "1",
                "Validation Result": "Correct",
                "Suggested Status": "Call Again",
                "last 10 comments": "ok",
            },
            {
                "account no": "2",
                "Validation Result": "Wrong",
                "Suggested Status": "No Potential",
                "last 10 comments": "x",
            },
        ]
    )
    assert report["statistics"]["total"] == 2
    assert report["statistics"]["correct"] == 1
    assert any(e["expectation"] == "expect_wrong_rate_below" for e in report["expectations"])


def test_cascade_soft_money():
    result = cascade_comment(
        "dont have money will get salary then proceed",
        min_fuzzy=50.0,
    )
    assert "money" in result["families"]
    assert result["pattern"].startswith("rules")
    # fuzzy or ml may decide; at least stages ran
    assert "fuzzy" in result
    assert "ml" in result


def test_cascade_enrich_sets_flag_or_status():
    lead = cascade_enrich_lead(
        {
            "account no": "T2",
            "customer status": "Call Again",
            "Suggested Status": "No Potential",
            "Validation Result": "Wrong",
            "last 10 comments": "no money until salary then will start",
        },
        min_fuzzy=50.0,
    )
    assert "quality_cascade" in lead
    assert "_needs_llm" in lead


def test_ml_predict_does_not_crash():
    pred = predict_status("no english only mandarin")
    assert "matched" in pred
    assert "backend" in pred
