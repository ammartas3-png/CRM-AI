import json
import logging
import os
import re
from typing import Any, Optional
from urllib.parse import unquote

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

DEFAULT_DATABASE_WEBHOOK_URL = (
    "https://ammartd20.app.n8n.cloud/webhook-test/Database-check"
)
ALLOWED_EXTENSIONS = {".xls", ".xlsx"}
ALLOWED_MIME_TYPES = {
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI()


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_BOT_TOKEN environment variable is required.",
        )
    return token


def _is_excel_file(file_name: str, mime_type: str) -> bool:
    normalized_name = (file_name or "").lower()
    normalized_mime_type = (mime_type or "").lower()
    return any(
        normalized_name.endswith(ext) for ext in ALLOWED_EXTENSIONS
    ) or normalized_mime_type in ALLOWED_MIME_TYPES


def _extract_filename(content_disposition: str, fallback_name: str) -> str:
    if not content_disposition:
        return fallback_name

    utf8_match = re.search(
        r"filename\*=UTF-8''(?P<name>[^;]+)",
        content_disposition,
        flags=re.IGNORECASE,
    )
    if utf8_match:
        return unquote(utf8_match.group("name")).strip('"')

    plain_match = re.search(
        r'filename=(?P<quote>"?)(?P<name>[^";]+)(?P=quote)',
        content_disposition,
        flags=re.IGNORECASE,
    )
    if plain_match:
        return plain_match.group("name")

    return fallback_name


async def _telegram_api_request(
    token: str,
    method: str,
    *,
    json_payload: Optional[dict[str, Any]] = None,
    data: Optional[dict[str, Any]] = None,
    files: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=json_payload, data=data, files=files)

    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error for {method}: {payload}")

    return payload.get("result", {})


async def _send_text_message(
    token: str,
    chat_id: int,
    text: str,
    reply_markup: Optional[dict[str, Any]] = None,
) -> None:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    await _telegram_api_request(token, "sendMessage", json_payload=payload)


async def _send_document_message(
    token: str,
    chat_id: int,
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
) -> None:
    files = {
        "document": (
            file_name,
            file_bytes,
            mime_type or "application/octet-stream",
        )
    }
    data = {"chat_id": str(chat_id), "caption": "Database check result"}
    await _telegram_api_request(
        token,
        "sendDocument",
        data=data,
        files=files,
    )


async def _download_telegram_file(token: str, file_id: str) -> bytes:
    file_meta = await _telegram_api_request(
        token,
        "getFile",
        json_payload={"file_id": file_id},
    )
    file_path = file_meta.get("file_path")
    if not file_path:
        raise RuntimeError("Telegram getFile response did not include file_path.")

    download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(download_url)
    response.raise_for_status()
    return response.content


async def _send_to_processing_webhook(
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
) -> tuple[str, str, bytes]:
    webhook_url = os.getenv("DATABASE_CHECK_WEBHOOK_URL", DEFAULT_DATABASE_WEBHOOK_URL)
    files = {
        "file": (
            file_name,
            file_bytes,
            mime_type or "application/octet-stream",
        )
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(webhook_url, files=files)

    response.raise_for_status()
    return (
        response.headers.get("content-type", "").lower(),
        response.headers.get("content-disposition", ""),
        response.content,
    )


async def _handle_start(token: str, chat_id: int) -> None:
    await _send_text_message(
        token,
        chat_id,
        "Welcome! Tap the button below to start database check.",
        reply_markup={
            "inline_keyboard": [
                [{"text": "Database check", "callback_data": "database_check"}]
            ]
        },
    )


async def _handle_callback_query(token: str, callback_query: dict[str, Any]) -> None:
    callback_id = callback_query.get("id")
    callback_data = callback_query.get("data")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")

    if callback_id:
        await _telegram_api_request(
            token,
            "answerCallbackQuery",
            json_payload={"callback_query_id": callback_id},
        )

    if callback_data == "database_check" and chat_id is not None:
        await _send_text_message(
            token,
            int(chat_id),
            "Please send your Excel file (.xls or .xlsx).",
        )


async def _handle_document_message(
    token: str,
    chat_id: int,
    document: dict[str, Any],
) -> None:
    file_name = document.get("file_name") or "database.xlsx"
    mime_type = document.get("mime_type") or ""

    if not _is_excel_file(file_name, mime_type):
        await _send_text_message(
            token,
            chat_id,
            "This is not an Excel file. Please send .xls or .xlsx file.",
        )
        return

    await _send_text_message(token, chat_id, "File received. Processing...")

    file_id = document.get("file_id")
    if not file_id:
        raise RuntimeError("Telegram document payload did not include file_id.")

    file_bytes = await _download_telegram_file(token, file_id)
    content_type, content_disposition, response_body = await _send_to_processing_webhook(
        file_name=file_name,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    if "application/json" in content_type:
        try:
            parsed_payload = json.loads(response_body.decode("utf-8"))
            if isinstance(parsed_payload, dict):
                message_text = parsed_payload.get("message") or parsed_payload.get("text")
                if message_text:
                    await _send_text_message(token, chat_id, str(message_text))
                else:
                    await _send_text_message(
                        token,
                        chat_id,
                        json.dumps(parsed_payload, indent=2),
                    )
            else:
                await _send_text_message(token, chat_id, str(parsed_payload))
        except Exception:
            await _send_text_message(
                token,
                chat_id,
                response_body.decode("utf-8", errors="replace"),
            )
        return

    if content_type.startswith("text/"):
        await _send_text_message(
            token,
            chat_id,
            response_body.decode("utf-8", errors="replace"),
        )
        return

    response_file_name = _extract_filename(
        content_disposition,
        f"processed_{file_name}",
    )
    await _send_document_message(
        token=token,
        chat_id=chat_id,
        file_name=response_file_name,
        file_bytes=response_body,
        mime_type=content_type,
    )


async def _handle_update(token: str, update: dict[str, Any]) -> None:
    callback_query = update.get("callback_query")
    if callback_query:
        await _handle_callback_query(token, callback_query)
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    if chat_id is None:
        return

    text = message.get("text")
    if isinstance(text, str) and text.startswith("/start"):
        await _handle_start(token, int(chat_id))
        return

    document = message.get("document")
    if document:
        await _handle_document_message(token, int(chat_id), document)


@app.get("/")
async def healthcheck() -> dict[str, Any]:
    return {"ok": True, "message": "Telegram webhook endpoint is running."}


@app.post("/")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
) -> JSONResponse:
    token = _get_bot_token()
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret.")

    try:
        update = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc

    try:
        await _handle_update(token, update)
    except Exception:
        logger.exception("Failed to process Telegram update.")
        return JSONResponse(
            status_code=200,
            content={"ok": False, "error": "Failed to process update."},
        )

    return JSONResponse(status_code=200, content={"ok": True})
