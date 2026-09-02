import base64
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from crm_classify import classify_leads, write_classify_run_note
from engine import run_zero_token_validation, write_run_note

app = FastAPI(title="Zero-Token Rule Engine", version="1.1.0")

VAULT_RUNS = Path(os.getenv("VAULT_RUNS_DIR", "/app/vault/runs"))


class ClassifyRequest(BaseModel):
    leads: list[dict[str, Any]] = Field(default_factory=list)
    source: Optional[str] = "n8n-v2"
    write_vault: bool = True


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "rule-engine",
        "token_cost": 0,
        "endpoints": ["/rules/validate", "/rules/classify-leads"],
    }


@app.post("/rules/classify-leads")
async def classify_leads_endpoint(body: ClassifyRequest) -> JSONResponse:
    if not body.leads:
        raise HTTPException(status_code=400, detail="leads array is required")
    result = classify_leads(body.leads)
    vault_note = ""
    if body.write_vault:
        vault_note = str(write_classify_run_note(VAULT_RUNS, result, source=body.source or "classify"))
    result["vault_note"] = vault_note
    result["source"] = body.source
    return JSONResponse(result)


@app.post("/rules/validate")
async def validate(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(default=None),
    chat_id: Optional[str] = Form(default=None),
) -> JSONResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = run_zero_token_validation(file.filename or "upload.xlsx", raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    note_path = write_run_note(VAULT_RUNS, result, source_name=file.filename or "upload.xlsx")

    return JSONResponse(
        {
            "ok": True,
            "valid": result.valid,
            "message": result.message,
            "issues": result.issues,
            "stats": result.stats,
            "ai_needed_rows": result.ai_needed_rows,
            "vault_note": str(note_path),
            "context": {"user_id": user_id, "chat_id": chat_id},
            "artifacts": {
                "csv_filename": result.corrected_filename,
                "csv_text": result.corrected_csv,
                "csv_base64": base64.b64encode(result.corrected_csv.encode("utf-8")).decode("ascii"),
            },
            "next_step": (
                "done"
                if result.valid
                else "send_ai_needed_rows_to_v2_verifier"
            ),
        }
    )
