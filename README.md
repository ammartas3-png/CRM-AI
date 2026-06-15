# CRM-AI Telegram Bot

This project contains a Telegram bot with the following flow:

1. User sends `/start`
2. Bot shows a **Database check** button
3. User taps the button, bot asks for an Excel file
4. Bot uploads the file to:
   `https://ammartd20.app.n8n.cloud/webhook-test/Database-check`
5. Bot sends the webhook response back to the same Telegram user

## Requirements

- Python 3.10+

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Export your bot token:

   ```bash
   export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
   ```

3. (Optional) Override webhook URL:

   ```bash
   export DATABASE_CHECK_WEBHOOK_URL="https://ammartd20.app.n8n.cloud/webhook-test/Database-check"
   ```

## Run

```bash
python bot.py
```
