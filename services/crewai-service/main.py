import base64
import io
import json
import os
import sys
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.file_convert import csv_preview_rows, normalize_upload_to_csv
from validation_tools import run_rule_based_validation

app = FastAPI(title="Database Check CrewAI Service", version="1.0.0")


def _build_crew_report(csv_text: str, validation: dict[str, Any]) -> str:
    llm_model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        issues = validation.get("issues") or []
        if validation.get("valid"):
            return (
                "Database check completed successfully.\n"
                f"Rows: {validation.get('non_empty_rows', 0)}, "
                f"Columns: {validation.get('columns', 0)}"
            )
        return "Database check found issues:\n- " + "\n- ".join(issues)

    try:
        from crewai import Agent, Crew, Process, Task

        validator = Agent(
            role="Database Validator",
            goal="Analyze CSV database files and identify structural/data quality issues.",
            backstory=(
                "You are a meticulous data quality engineer focused on CRM/database imports."
            ),
            verbose=False,
            allow_delegation=False,
        )
        reporter = Agent(
            role="Validation Reporter",
            goal="Write concise Turkish/English user-friendly validation summaries.",
            backstory=(
                "You translate technical validation output into clear action items for business users."
            ),
            verbose=False,
            allow_delegation=False,
        )

        preview = csv_preview_rows(csv_text, limit=8)
        validation_task = Task(
            description=(
                "Review this validation JSON and CSV preview. "
                "Confirm issues and add practical recommendations.\n\n"
                f"Validation JSON:\n{json.dumps(validation, ensure_ascii=False)}\n\n"
                f"CSV preview:\n{json.dumps(preview, ensure_ascii=False)}"
            ),
            expected_output="Structured bullet list of confirmed issues and recommendations.",
            agent=validator,
        )
        report_task = Task(
            description=(
                "Create a short user message (max 12 lines) summarizing validation results. "
                "If valid, confirm success. If invalid, list top fixes."
            ),
            expected_output="Plain text message suitable for Telegram.",
            agent=reporter,
            context=[validation_task],
        )

        crew = Crew(
            agents=[validator, reporter],
            tasks=[validation_task, report_task],
            process=Process.sequential,
            verbose=False,
        )
        result = crew.kickoff()
        return str(result)
    except Exception as exc:
        issues = validation.get("issues") or []
        fallback = (
            "Database check completed with fallback mode (CrewAI unavailable).\n"
            f"Model target: {llm_model}\n"
        )
        if validation.get("valid"):
            return fallback + "Status: VALID"
        return fallback + "Issues:\n- " + "\n- ".join(issues) + f"\n\nError: {exc}"


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "crewai-service",
        "crewai_enabled": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


@app.post("/validate")
async def validate_database_file(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(default=None),
    chat_id: Optional[str] = Form(default=None),
    source: Optional[str] = Form(default="telegram"),
) -> JSONResponse:
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        csv_name, csv_text, csv_bytes = normalize_upload_to_csv(
            file_name=file.filename or "upload.xlsx",
            file_bytes=raw_bytes,
            mime_type=file.content_type or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    validation = run_rule_based_validation(csv_text)
    report_message = _build_crew_report(csv_text, validation)

    response_payload: dict[str, Any] = {
        "ok": True,
        "valid": validation.get("valid", False),
        "message": report_message,
        "validation": validation,
        "converted": {
            "from": file.filename,
            "to": csv_name,
            "format": "csv",
        },
        "context": {
            "user_id": user_id,
            "chat_id": chat_id,
            "source": source,
        },
        "artifacts": {
            "csv_text": csv_text,
            "csv_base64": base64.b64encode(csv_bytes).decode("ascii"),
            "csv_filename": csv_name,
        },
    }

    return JSONResponse(status_code=200, content=response_payload)


@app.post("/validate-csv-text")
async def validate_csv_text(payload: dict[str, Any]) -> JSONResponse:
    csv_text = str(payload.get("csv_text", ""))
    if not csv_text.strip():
        raise HTTPException(status_code=400, detail="csv_text is required.")

    validation = run_rule_based_validation(csv_text)
    report_message = _build_crew_report(csv_text, validation)
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "valid": validation.get("valid", False),
            "message": report_message,
            "validation": validation,
        },
    )
