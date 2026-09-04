"""Rules → Fuzzy → SetFit → LLM-flag cascade (support-ticket-classifier pattern).

Does not call an LLM itself; sets `_needs_llm` when earlier stages are weak so
n8n AI Agent / smart-layer can pick the lead up.
"""

from __future__ import annotations

from typing import Any

from noise_strip import strip_noise
from router import detect_families, fold, route_comment
from setfit_router import predict_status


def cascade_comment(comments: str, *, min_fuzzy: float = 62.0, min_ml: float = 45.0) -> dict[str, Any]:
    noise = strip_noise(comments)
    cleaned = noise["cleaned"] or comments
    fams = detect_families(cleaned)

    # Stage 1: family heuristic (rules)
    rule_hit = bool(fams)

    # Stage 2: RapidFuzz example bank
    family = None
    for pref in ("language", "refusal", "money", "callback"):
        if pref in fams:
            family = pref
            break
    fuzzy = route_comment(cleaned, family=family, min_score=min_fuzzy)

    # Stage 3: SetFit / sklearn
    ml = predict_status(cleaned)

    decided = None
    stage = "none"
    score = 0.0
    if fuzzy.get("matched") and fuzzy.get("status"):
        decided = fuzzy["status"]
        stage = "fuzzy"
        score = float(fuzzy.get("score") or 0)
    elif ml.get("matched") and ml.get("status") and float(ml.get("score") or 0) >= min_ml:
        decided = ml["status"]
        stage = "setfit_or_sklearn"
        score = float(ml.get("score") or 0)

    needs_llm = decided is None and (rule_hit or len(fold(cleaned)) > 40)

    return {
        "comments_cleaned": cleaned,
        "noise": {"backend": noise["backend"], "chars_removed_approx": noise["chars_removed_approx"]},
        "families": fams,
        "rule_hit": rule_hit,
        "fuzzy": fuzzy,
        "ml": ml,
        "status": decided,
        "stage": stage,
        "score": score,
        "needs_llm": needs_llm,
        "pattern": "rules→fuzzy→setfit→llm-flag",
        "inspired_by": "support-ticket-classifier hybrid cascade",
    }


def cascade_enrich_lead(lead: dict[str, Any], *, min_fuzzy: float = 62.0) -> dict[str, Any]:
    comments = str(
        lead.get("last 10 comments")
        or lead.get("last_10_comments")
        or lead.get("comments")
        or ""
    )
    out = dict(lead)
    result = cascade_comment(comments, min_fuzzy=min_fuzzy)
    out["quality_cascade"] = result
    out["_needs_llm"] = bool(result.get("needs_llm"))
    if result.get("status"):
        vr = str(lead.get("Validation Result") or "").lower()
        engine = fold(str(lead.get("Suggested Status") or ""))
        if vr in {"manual check", "manual", "wrong"} or engine in {
            "call again",
            "no potential",
            "recall",
            "no answer 1-5",
            "no interest",
        }:
            out["Suggested Status"] = result["status"]
            out["Decision Source"] = f"Quality Cascade:{result['stage']}"
            out["Reason"] = (
                f"cascade {result['stage']} score={result['score']} "
                f"families={result.get('families')}"
            )
            crm = fold(str(lead.get("customer status") or lead.get("customer_status") or ""))
            out["Validation Result"] = (
                "Correct"
                if fold(result["status"]) == crm
                else ("Manual Check" if float(result["score"]) < 70 else "Wrong")
            )
            out["_quality_cascade_applied"] = True
    return out
