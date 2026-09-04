"""CRM Quality Layer API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from cascade import cascade_comment, cascade_enrich_lead
from conflicts import build_conflict_report, write_report
from noise_strip import strip_noise
from review_queue import (
    enqueue_correct_sample,
    export_argilla_records,
    list_pending,
    maybe_push_argilla,
    record_verdict,
)
from router import detect_families, enrich_lead, route_comment
from run_checkpoint import run_checkpoint, write_checkpoint
from schema_gate import pandera_schema_available, validate_leads
from setfit_router import ensure_model, predict_status

app = FastAPI(title="CRM Quality Layer", version="1.1.0")
ROOT = Path(__file__).resolve().parents[2]

UPSTREAM_REPOS = [
    "https://github.com/aurelio-labs/semantic-router",
    "https://github.com/argilla-io/argilla",
    "https://github.com/snorkel-team/snorkel",
    "https://github.com/567-labs/instructor",
    "https://github.com/vi3k6i5/flashtext",
    "https://github.com/rapidfuzz/RapidFuzz",
    "https://github.com/huggingface/setfit",
    "https://github.com/explosion/spaCy",
    "https://github.com/unionai-oss/pandera",
    "https://github.com/ksploitx/support-ticket-classifier",
    "https://github.com/great-expectations/great_expectations",
    "https://github.com/erinozolins/eval-loop",
    "https://github.com/yablokolabs/CallLens",
    "https://github.com/attentiontech/gtm-superintelligence",
    "https://github.com/aiagentwithdhruv/dealpulse",
]


@app.get("/health")
def health() -> dict[str, Any]:
    ml_backend = ensure_model()
    return {
        "ok": True,
        "service": "quality-layer",
        "version": "1.1.0",
        "features": [
            "ambiguous-router",
            "correct-bucket-review",
            "conflict-matrix",
            "argilla-export",
            "noise-strip",
            "schema-gate",
            "setfit-or-sklearn-router",
            "cascade",
            "run-checkpoint",
        ],
        "backends": {
            "ml_router": ml_backend,
            "pandera_available": pandera_schema_available(),
        },
        "upstream_repos": UPSTREAM_REPOS,
    }


@app.post("/quality/route")
def quality_route(payload: dict[str, Any]) -> JSONResponse:
    comments = str(payload.get("comments") or payload.get("last 10 comments") or "")
    family = payload.get("family")
    min_score = float(payload.get("min_score") or 62)
    return JSONResponse(route_comment(comments, family=family, min_score=min_score))


@app.post("/quality/strip-noise")
def quality_strip_noise(payload: dict[str, Any]) -> JSONResponse:
    comments = str(payload.get("comments") or payload.get("last 10 comments") or "")
    use_spacy = bool(payload.get("use_spacy", True))
    return JSONResponse(strip_noise(comments, use_spacy=use_spacy))


@app.post("/quality/validate-leads")
def quality_validate_leads(payload: dict[str, Any]) -> JSONResponse:
    leads = payload.get("leads") or payload.get("items") or []
    if isinstance(leads, dict):
        leads = [leads]
    return JSONResponse(validate_leads(list(leads)))


@app.post("/quality/predict-ml")
def quality_predict_ml(payload: dict[str, Any]) -> JSONResponse:
    comments = str(payload.get("comments") or payload.get("last 10 comments") or "")
    return JSONResponse(predict_status(comments))


@app.post("/quality/cascade")
def quality_cascade(payload: dict[str, Any]) -> JSONResponse:
    comments = str(payload.get("comments") or payload.get("last 10 comments") or "")
    min_fuzzy = float(payload.get("min_fuzzy") or payload.get("min_score") or 62)
    min_ml = float(payload.get("min_ml") or 45)
    return JSONResponse(cascade_comment(comments, min_fuzzy=min_fuzzy, min_ml=min_ml))


@app.post("/quality/checkpoint")
def quality_checkpoint(payload: dict[str, Any]) -> JSONResponse:
    leads = payload.get("leads") or payload.get("items") or []
    if isinstance(leads, dict):
        leads = [leads]
    report = run_checkpoint(list(leads))
    data_dir = Path(os.getenv("QUALITY_DATA_DIR", str(ROOT / "evals")))
    out = data_dir / "run_checkpoint.json"
    try:
        write_checkpoint(report, out)
        report["written_to"] = str(out)
    except Exception as exc:
        report["written_to"] = None
        report["write_error"] = str(exc)
    return JSONResponse(report)


@app.post("/quality/enrich-leads")
def enrich_leads(payload: dict[str, Any]) -> JSONResponse:
    leads = payload.get("leads") or payload.get("items") or []
    if isinstance(leads, dict):
        leads = [leads]
    min_score = float(payload.get("min_score") or 62)
    only_ambiguous = bool(payload.get("only_ambiguous", True))
    use_cascade = bool(payload.get("use_cascade", False))
    strip_first = bool(payload.get("strip_noise", True))
    out: list[dict[str, Any]] = []
    applied = 0
    for lead in leads:
        comments = str(lead.get("last 10 comments") or lead.get("comments") or "")
        work = dict(lead)
        if strip_first and comments:
            cleaned = strip_noise(comments)["cleaned"]
            if cleaned != comments:
                work["_comments_raw"] = comments
                work["last 10 comments"] = cleaned
                comments = cleaned
        fams = detect_families(comments)
        vr = str(work.get("Validation Result") or "").lower()
        conf = str(work.get("Confidence") or "").lower()
        needs = (
            vr in {"manual check", "manual", "wrong"}
            or conf == "low"
            or bool(work.get("_needs_bot_qa"))
            or bool(fams)
        )
        if only_ambiguous and not needs:
            out.append(work)
            continue
        if use_cascade:
            enriched = cascade_enrich_lead(work, min_fuzzy=min_score)
            if enriched.get("_quality_cascade_applied"):
                applied += 1
        else:
            enriched = enrich_lead(work, min_score=min_score)
            if enriched.get("_quality_router_applied"):
                applied += 1
        out.append(enriched)
    return JSONResponse(
        {
            "ok": True,
            "count": len(out),
            "applied": applied,
            "mode": "cascade" if use_cascade else "fuzzy-router",
            "leads": out,
        }
    )


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
