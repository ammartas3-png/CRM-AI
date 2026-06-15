# CRM-AI Telegram Bot (Vercel Webhook)

This project is configured for **Vercel deployment** using Telegram webhooks.

## Bot flow

1. User sends `/start`
2. Bot returns an inline button: **Database check**
3. User taps the button and bot asks for an Excel file (`.xls` / `.xlsx`)
4. Bot sends that file to:
   `https://ammartd20.app.n8n.cloud/webhook-test/Database-check`
5. Bot returns the webhook response back to the same user
   - text/JSON responses are sent as a message
   - binary responses are sent as a Telegram document

## Endpoints

- `/` - deployment landing page with setup links
- `POST /api/telegram` - Telegram webhook receiver
- `GET /api/set_webhook` - One-click webhook registration helper
- `GET /api/webhook_info` - show Telegram webhook status

## Required Vercel environment variables

- `TELEGRAM_BOT_TOKEN` (required)

## Optional environment variables

- `DATABASE_CHECK_WEBHOOK_URL`
  - default: `https://ammartd20.app.n8n.cloud/webhook-test/Database-check`
- `APP_BASE_URL`
  - example: `https://your-project-name.vercel.app`
  - used by `/api/set_webhook` when it cannot infer host headers
- `TELEGRAM_WEBHOOK_SECRET`
  - optional security header for Telegram webhook requests
- `WEBHOOK_SETUP_KEY`
  - optional key to protect `/api/set_webhook`

## Deploy on Vercel

1. Import this repository into Vercel.
2. Set at least:
   - `TELEGRAM_BOT_TOKEN`
3. Deploy.
4. Register Telegram webhook:
   - Open:
     - `https://<your-vercel-domain>/api/set_webhook`
   - If you configured `WEBHOOK_SETUP_KEY`:
     - `https://<your-vercel-domain>/api/set_webhook?key=<your_key>`
5. Confirm it returns `"ok": true`.

After this, your bot is live on Vercel.

## Troubleshooting (bot not responding)

1. Check function is reachable:
   - `https://<your-vercel-domain>/api/telegram`
   - should return a JSON health message
2. Register webhook again:
   - `https://<your-vercel-domain>/api/set_webhook`
3. Verify webhook status:
   - `https://<your-vercel-domain>/api/webhook_info`
   - ensure `url` matches your Vercel domain and `last_error_message` is empty
4. If you use `WEBHOOK_SETUP_KEY`, include:
   - `?key=<your_key>` on `set_webhook` and `webhook_info` URLs
