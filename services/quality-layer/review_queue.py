"""Correct-bucket human review queue + Argilla-compatible export."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _root() -> Path:
    return Path(os.getenv("QUALITY_DATA_DIR", "/app/data"))


def queue_path() -> Path:
    p = _root() / "review_queue"
    p.mkdir(parents=True, exist_ok=True)
    return p / "queue.jsonl"


def verdicts_path() -> Path:
    p = _root() / "review_queue"
    p.mkdir(parents=True, exist_ok=True)
    return p / "verdicts.jsonl"


def enqueue_correct_sample(leads: list[dict[str, Any]], *, limit: int = 50) -> dict[str, Any]:
    picked: list[dict[str, Any]] = []
    for lead in leads:
        vr = str(lead.get("Validation Result") or lead.get("validation_result") or "").lower()
        crm = str(lead.get("customer status") or "")
        sug = str(lead.get("Suggested Status") or lead.get("suggested_status") or "")
        if vr == "correct" or (crm and sug and crm.strip().lower() == sug.strip().lower()):
            picked.append(lead)
        if len(picked) >= limit:
            break

    qp = queue_path()
    now = datetime.now(timezone.utc).isoformat()
    written = 0
    with qp.open("a", encoding="utf-8") as f:
        for lead in picked:
            rec = {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "bucket": "correct",
                "account_no": lead.get("account no") or lead.get("account_no"),
                "customer_status": lead.get("customer status"),
                "suggested_status": lead.get("Suggested Status") or lead.get("suggested_status"),
                "reason": lead.get("Reason") or lead.get("reason"),
                "comments": lead.get("last 10 comments") or lead.get("comments"),
                "status": "pending",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    return {"ok": True, "enqueued": written, "path": str(qp)}


def list_pending(limit: int = 20) -> list[dict[str, Any]]:
    qp = queue_path()
    if not qp.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in qp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("status") == "pending":
            out.append(rec)
        if len(out) >= limit:
            break
    return out


def record_verdict(item_id: str, human_status: str, note: str = "") -> dict[str, Any]:
    vp = verdicts_path()
    rec = {
        "id": item_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "human_status": human_status,
        "note": note,
    }
    with vp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    qp = queue_path()
    if qp.exists():
        rows = []
        for line in qp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("id") == item_id:
                r["status"] = "reviewed"
                r["human_status"] = human_status
            rows.append(r)
        qp.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )
    return {"ok": True, "verdict": rec}


def export_argilla_records(limit: int = 500) -> list[dict[str, Any]]:
    pending = list_pending(limit=limit)
    records = []
    for r in pending:
        records.append(
            {
                "text": r.get("comments") or "",
                "metadata": {
                    "account_no": r.get("account_no"),
                    "customer_status": r.get("customer_status"),
                    "suggested_status": r.get("suggested_status"),
                    "reason": r.get("reason"),
                    "bucket": r.get("bucket"),
                    "queue_id": r.get("id"),
                },
                "suggestion": {
                    "agent": "memory-match",
                    "label": r.get("suggested_status"),
                },
            }
        )
    return records


def maybe_push_argilla(records: list[dict[str, Any]]) -> dict[str, Any]:
    url = os.getenv("ARGILLA_API_URL", "").strip()
    key = os.getenv("ARGILLA_API_KEY", "").strip()
    workspace = os.getenv("ARGILLA_WORKSPACE", "crm-ai")
    dataset = os.getenv("ARGILLA_DATASET", "correct-bucket-review")
    out = _root() / "review_queue" / f"argilla_export_{dataset}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workspace": workspace,
        "dataset": dataset,
        "records": records,
    }
    if url:
        payload["api_url"] = url
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "pushed": bool(url and key),
        "mode": "export_file",
        "path": str(out),
        "count": len(records),
        "note": "Import JSON into Argilla UI, or set ARGILLA_API_URL/KEY for server push later",
    }
