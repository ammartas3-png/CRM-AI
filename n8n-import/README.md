# n8n Import Dosyalari

## Canli sistem (API ile uygulandi)

n8n Cloud uzerinde su an aktif:
1. `Telegram Front Door -> V2 Database-check` — `/start`, dosya alir, `chat_id` + file'i V2 webhook'a multipart POST eder
2. `Telegram Database Validator Bot V2` (smart upgraded) — dinamik `chat_id`, sheet governance, Manual Entry closed-loop, agent score

## Snapshot dosyalari

- `06-Front-Door-Telegram.workflow.json` — Front Door (chat_id forward dahil)
- `05-V2-smart-upgraded.workflow.json` — guncel V2 yedegi
- `04-...CSV_first_fixed...` — onceki CSV fix
- `Telegram_Database_Validator_Bot_V2.original.json` — orijinal

Detay: `docs/SMART-UPGRADES.md`, `docs/RULE-ENGINE-INTEGRATION.md`
