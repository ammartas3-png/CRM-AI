# Smart upgrades applied to V2

Live n8n workflow `Telegram Database Validator Bot V2` now includes:

1. CSV/XLSX/XLS/JSON extract path (File Kind Switch)
2. Telegram Front Door workflow for `/start` + file upload
3. Cheaper AI batches (short comments, batch=15)
4. Instructor-like JSON repair after AI Agent
5. Stricter Verifier gate (skip deterministic Correct / no-answer)
6. Models switched to `gpt-5.4-mini`
7. Stronger prompt-injection resistant system prompt
8. Confidence / Auto Accept enrichment (Smart Trace)
9. Telegram summary message before XLSX reports
10. Decision Memory Logger + Google Sheets `Decision_Memory` append
11. Rule Hit Tracker in workflow staticData

## Supporting GitHub-inspired layers in repo

- `vault/` Obsidian-like markdown memory
- `services/rule-engine` zero-token fixes
- `services/smart-layer` Pandera + Instructor helpers
- `services/memory-service` MCP-compatible graph memory

## Important Google Sheet setup

Create a tab named exactly `Decision_Memory` in spreadsheet `CRM_AI_Rules`.
If missing, append node continues without failing the run.
