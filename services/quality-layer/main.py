"""CRM Quality Layer API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from conflicts import build_conflict_report, write_report
from review_queue import (
    enqueue_correct_sample,
    export_argilla_records,
    list_pending,
    maybe_push_argilla,
    record_verdict,
)
from router import detect_families, enrich_lead, route_comment

app = FastAPI(title="CRM Quality Layer", version="1.0.0")
ROOT = Path(__file__).resolve().parents[2]


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "quality-layer",
        "features": [
            "ambiguous-router",
            "correct-bucket-review",
            "conflict-matrix",
            "argilla-export",
        ],
        "upstream_repos": [
            "https://github.com/aurelio-labs/semantic-router",
            "https://github.com/argilla-io/argilla",
            "https://github.com/snorkel-team/snorkel",
            "https://github.com/567-labs/instructor",
            "https://github.com/vi3k6i5/flashtext",
        ],
    }


@app.post("/quality/route")
def quality_route(payload: dict[str, Any]) -> JSONResponse:
    comments = str(payload.get("comments") or payload.get("last 10 comments") or "")
    family = payload.get("family")
    min_score = float(payload.get("min_score") or 62)
    return JSONResponse(route_comment(comments, family=family, min_score=min_score))


@app.post("/quality/enrich-leads")
def enrich_leads(payload: dict[str, Any]) -> JSONResponse:
    leads = payload.get("leads") or payload.get("items") or []
    if isinstance(leads, dict):
        leads = [leads]
    min_score = float(payload.get("min_score") or 62)
    only_ambiguous = bool(payload.get("only_ambiguous", True))
    out: list[dict[str, Any]] = []
    applied = 0
    for lead in leads:
        comments = str(lead.get("last 10 comments") or lead.get("comments") or "")
        fams = detect_families(comments)
        vr = str(lead.get("Validation Result") or "").lower()
        conf = str(lead.get("Confidence") or "").lower()
        needs = (
            vr in {"manual check", "manual", "wrong"}
            or conf == "low"
            or bool(lead.get("_needs_bot_qa"))
            or bool(fams)
        )
        if only_ambiguous and not needs:
            out.append(lead)
            continue
        enriched = enrich_lead(lead, min_score=min_score)
        if enriched.get("_quality_router_applied"):
            applied += 1
        out.append(enriched)
    return JSONResponse({"ok": True, "count": len(out), "applied": applied, "leads": out})


@app.post("/quality/review/enqueue-correct")
def review_enqueue(payload: dict[str, Any]) -> JSONResponse:
    leads = payload.get("leads") or []
    limit = int(payload.get("limit") or 50)
    result = enqueue_correct_sample(leads, limit=limit)
    records = export_argilla_records(limit=limit)
    result["argilla"] = maybe_push_argilla(records)
    result["argilla_records"] = len(records)
    return JSONResponse(result)


@app.get("/quality/review/pending")
def review_pending(limit: int = 20) -> JSONResponse:
    return JSONResponse({"ok": True, "items": list_pending(limit=limit)})


@app.post("/quality/review/verdict")
def review_verdict(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        record_verdict(
            str(payload.get("id") or ""),
            str(payload.get("human_status") or ""),
            str(payload.get("note") or ""),
        )
    )


@app.post("/quality/conflicts/report")
def conflicts_report(payload: dict[str, Any] | None = None) -> JSONResponse:
    payload = payload or {}
    candidates = [
        ROOT / "evals" / "golden_leads.jsonl",
        ROOT / "evals" / "wrong_review_cases.jsonl",
        Path("/app/evals") / "golden_leads.jsonl",
        Path("/app/evals") / "wrong_review_cases.jsonl",
    ]
    raw_paths = payload.get("paths") or []
    paths = [Path(p) for p in raw_paths] if raw_paths else []
    if not paths:
        seen: set[str] = set()
        for p in candidates:
            key = str(p.resolve()) if p.exists() else ""
            if p.exists() and key not in seen:
                paths.append(p)
                seen.add(key)
    report = build_conflict_report(paths)
    data_dir = Path(os.getenv("QUALITY_DATA_DIR", str(ROOT / "evals")))
    out = data_dir / "conflict_report.json"
    try:
        write_report(report, out)
        report["written_to"] = str(out)
    except Exception as exc:
        report["written_to"] = None
        report["write_error"] = str(exc)
    return JSONResponse({"ok": True, "report": report, "sources": [str(p) for p in paths]})
