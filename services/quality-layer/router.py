"""Lightweight fuzzy router for ambiguous CRM comments."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

from routes_bank import ROUTE_BANK, all_examples

_WS = re.compile(r"\s+")
_TR = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "ğ": "g",
        "ç": "c",
        "ö": "o",
        "ü": "u",
        "Ş": "s",
        "Ğ": "g",
        "Ç": "c",
        "Ö": "o",
        "Ü": "u",
    }
)


def fold(text: str) -> str:
    t = str(text or "").lower().translate(_TR)
    t = t.replace("\n", " ").replace("|", " ")
    t = re.sub(r"[;'\"`.]", "", t)
    return _WS.sub(" ", t).strip()


def detect_families(comments: str) -> list[str]:
    t = fold(comments)
    fams: list[str] = []
    if re.search(
        r"\b(no money|dont have money|cant afford|cannot afford|no funds|dont have the funds|no capital)\b",
        t,
    ):
        fams.append("money")
    if re.search(
        r"\b(cb\b|callback|call back|call again|called back|call me later|call him later)\b",
        t,
    ):
        fams.append("callback")
    if re.search(
        r"\b(not interest|no interest|dont want|leave it|playing around|scam|cancel|lets stop|registered by mistake)\b",
        t,
    ):
        fams.append("refusal")
    if re.search(
        r"\b(no english|no language|mandarin|only speaks|language barrier|huasa|bangla)\b",
        t,
    ):
        fams.append("language")
    return fams


def route_comment(
    comments: str,
    *,
    family: str | None = None,
    min_score: float = 62.0,
) -> dict[str, Any]:
    text = fold(comments)
    if not text:
        return {
            "matched": False,
            "route": None,
            "status": None,
            "score": 0.0,
            "reason": "empty comments",
        }

    candidates = all_examples()
    if family:
        fam = family.lower().strip()
        candidates = [
            (name, status, ex)
            for name, status, ex in candidates
            if ROUTE_BANK[name]["family"] == fam
        ]

    best: tuple[str, str, str, float] | None = None
    for name, status, ex in candidates:
        s = float(fuzz.token_set_ratio(text, fold(ex)))
        if best is None or s > best[3]:
            best = (name, status, ex, s)

    if best is None or best[3] < min_score:
        return {
            "matched": False,
            "route": best[0] if best else None,
            "status": None,
            "score": round(best[3], 2) if best else 0.0,
            "example": best[2] if best else None,
            "reason": "below threshold",
            "family": family,
        }

    return {
        "matched": True,
        "route": best[0],
        "status": best[1],
        "score": round(best[3], 2),
        "example": best[2],
        "reason": f"fuzzy match to route {best[0]}",
        "family": ROUTE_BANK[best[0]]["family"],
    }


def enrich_lead(lead: dict[str, Any], *, min_score: float = 62.0) -> dict[str, Any]:
    comments = str(
        lead.get("last 10 comments")
        or lead.get("last_10_comments")
        or lead.get("comments")
        or ""
    )
    engine_status = str(lead.get("Suggested Status") or lead.get("suggested_status") or "")
    crm = str(lead.get("customer status") or lead.get("customer_status") or "")
    fams = detect_families(comments)
    out = dict(lead)
    out["_quality_router_applied"] = False

    if not fams:
        out["quality_router"] = {
            "applied": False,
            "reason": "no ambiguous family detected",
            "families": [],
        }
        return out

    priority = ["language", "refusal", "money", "callback"]
    family = next((f for f in priority if f in fams), fams[0])
    routed = route_comment(comments, family=family, min_score=min_score)
    out["quality_router"] = {
        "applied": bool(routed.get("matched")),
        "families": fams,
        "picked_family": family,
        **routed,
        "engine_status_before": engine_status,
        "crm_status": crm,
    }

    if not routed.get("matched") or not routed.get("status"):
        return out

    vr = str(lead.get("Validation Result") or lead.get("validation_result") or "").lower()
    suggest = str(routed["status"])
    if vr in {"manual check", "manual"} or fold(engine_status) in {
        "call again",
        "no potential",
        "recall",
        "no answer 1-5",
        "no interest",
    }:
        out["Suggested Status"] = suggest
        out["Decision Source"] = f"Quality Router:{routed['route']}"
        out["Reason"] = (
            f"Quality router ({routed['route']}, score={routed['score']}) "
            f"example≈'{(routed.get('example') or '')[:60]}'"
        )
        out["Validation Result"] = (
            "Correct"
            if fold(suggest) == fold(crm)
            else ("Manual Check" if float(routed["score"]) < 75 else "Wrong")
        )
        out["_quality_router_applied"] = True
    return out
