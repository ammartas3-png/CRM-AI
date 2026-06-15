import os
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

app = FastAPI()


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_BOT_TOKEN environment variable is required.",
        )
    return token


def _resolve_base_url(request: Request) -> str:
    configured_base = os.getenv("APP_BASE_URL", "").strip()
    if configured_base:
        return configured_base.rstrip("/")

    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")
    if not host:
        raise HTTPException(
            status_code=400,
            detail="Cannot infer deployment host. Set APP_BASE_URL env variable.",
        )

    return f"{forwarded_proto}://{host}".rstrip("/")


def _validate_setup_key_or_raise(key: Optional[str]) -> None:
    setup_key = os.getenv("WEBHOOK_SETUP_KEY", "").strip()
    if setup_key and key != setup_key:
        raise HTTPException(status_code=401, detail="Invalid setup key.")


async def _fetch_webhook_info(token: str) -> dict[str, Any]:
    telegram_api_base = f"https://api.telegram.org/bot{token}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        webhook_info_response = await client.get(f"{telegram_api_base}/getWebhookInfo")
        webhook_info_response.raise_for_status()
        webhook_info_payload = webhook_info_response.json()

    if not webhook_info_payload.get("ok"):
        raise HTTPException(
            status_code=500,
            detail=f"getWebhookInfo failed: {webhook_info_payload}",
        )

    return webhook_info_payload.get("result", {})


@app.get("/")
@app.get("/api/set_webhook")
@app.get("/api/set_webhook/")
async def set_webhook(
    request: Request,
    key: Optional[str] = Query(default=None),
    webhook_url: Optional[str] = Query(default=None),
) -> JSONResponse:
    _validate_setup_key_or_raise(key)

    token = _get_bot_token()
    final_webhook_url = webhook_url or f"{_resolve_base_url(request)}/api/telegram"
    secret_token = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()

    payload: dict[str, Any] = {
        "url": final_webhook_url,
        "allowed_updates": ["message", "callback_query"],
    }
    if secret_token:
        payload["secret_token"] = secret_token

    telegram_api_base = f"https://api.telegram.org/bot{token}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        set_webhook_response = await client.post(
            f"{telegram_api_base}/setWebhook",
            json=payload,
        )
        set_webhook_response.raise_for_status()
        set_webhook_payload = set_webhook_response.json()
    webhook_info_payload = {"ok": True, "result": await _fetch_webhook_info(token)}

    if not set_webhook_payload.get("ok"):
        raise HTTPException(
            status_code=500,
            detail=f"setWebhook failed: {set_webhook_payload}",
        )
    if not webhook_info_payload.get("ok"):
        raise HTTPException(
            status_code=500,
            detail=f"getWebhookInfo failed: {webhook_info_payload}",
        )

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "webhook_url": final_webhook_url,
            "set_webhook_result": set_webhook_payload.get("result"),
            "webhook_info": webhook_info_payload.get("result"),
        },
    )


@app.get("/api/webhook_info")
@app.get("/api/webhook_info/")
async def webhook_info(key: Optional[str] = Query(default=None)) -> JSONResponse:
    _validate_setup_key_or_raise(key)
    token = _get_bot_token()
    info = await _fetch_webhook_info(token)
    return JSONResponse(status_code=200, content={"ok": True, "webhook_info": info})
