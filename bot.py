import io
import json
import logging
import os
import re

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

DEFAULT_WEBHOOK_URL = (
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
        r"filename\*=UTF-8''(?P<name>[^;]+)", content_disposition, re.IGNORECASE
    )
    if utf8_match:
        return utf8_match.group("name").strip('"')

    plain_match = re.search(
        r'filename=(?P<quote>"?)(?P<name>[^";]+)(?P=quote)',
        content_disposition,
        re.IGNORECASE,
    )
    if plain_match:
        return plain_match.group("name")

    return fallback_name


async def _send_to_webhook(
    webhook_url: str, file_name: str, file_bytes: bytes
) -> tuple[str, str, bytes, str]:
    timeout = aiohttp.ClientTimeout(total=180)
    form = aiohttp.FormData()
    form.add_field(
        name="file",
        value=file_bytes,
        filename=file_name,
        content_type="application/octet-stream",
    )

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(webhook_url, data=form) as response:
            response_body = await response.read()
            if response.status >= 400:
                raise RuntimeError(
                    f"Webhook request failed ({response.status}): "
                    f"{response_body.decode(errors='replace')}"
                )

            content_type = response.headers.get("Content-Type", "").lower()
            disposition = response.headers.get("Content-Disposition", "")
            response_file_name = _extract_filename(
                disposition, f"processed_{file_name}"
            )
            return content_type, response_file_name, response_body, disposition


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Database check", callback_data="database_check")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["awaiting_excel"] = False
    await update.message.reply_text(
        "Welcome! Tap the button below to start database check.",
        reply_markup=reply_markup,
    )


async def database_check_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "database_check":
        context.user_data["awaiting_excel"] = True
        await query.message.reply_text(
            "Please send your Excel file (.xls or .xlsx)."
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_excel"):
        await update.message.reply_text(
            "Send /start and tap 'Database check' first."
        )
        return

    document = update.message.document
    if not _is_excel_file(document.file_name, document.mime_type):
        await update.message.reply_text(
            "This is not an Excel file. Please send .xls or .xlsx file."
        )
        return

    await update.message.reply_text("File received. Processing...")

    try:
        tg_file = await document.get_file()
        buffer = io.BytesIO()
        await tg_file.download_to_memory(out=buffer)
        file_bytes = buffer.getvalue()

        webhook_url = context.bot_data["webhook_url"]
        content_type, response_file_name, response_body, _ = await _send_to_webhook(
            webhook_url=webhook_url,
            file_name=document.file_name or "database.xlsx",
            file_bytes=file_bytes,
        )

        if "application/json" in content_type:
            parsed = json.loads(response_body.decode("utf-8"))
            if isinstance(parsed, dict):
                message_text = parsed.get("message") or parsed.get("text")
                if message_text:
                    await update.message.reply_text(str(message_text))
                else:
                    await update.message.reply_text(json.dumps(parsed, indent=2))
            else:
                await update.message.reply_text(str(parsed))
        elif content_type.startswith("text/"):
            await update.message.reply_text(
                response_body.decode("utf-8", errors="replace")
            )
        else:
            output = InputFile(io.BytesIO(response_body), filename=response_file_name)
            await update.message.reply_document(
                document=output,
                caption="Database check result",
            )

        context.user_data["awaiting_excel"] = False
    except Exception as exc:
        logger.exception("Failed to process user file: %s", exc)
        await update.message.reply_text(
            "Something went wrong while processing your file. Please try again."
        )


async def handle_non_document(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if context.user_data.get("awaiting_excel"):
        await update.message.reply_text(
            "Please upload an Excel file (.xls or .xlsx)."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error while processing update: %s", context.error)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("DATABASE_CHECK_WEBHOOK_URL", DEFAULT_WEBHOOK_URL)

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required.")

    app = ApplicationBuilder().token(token).build()
    app.bot_data["webhook_url"] = webhook_url

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(database_check_button))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO | filters.VIDEO | filters.AUDIO,
            handle_non_document,
        )
    )
    app.add_error_handler(error_handler)

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
