# CRM-AI — Cheap + Smart Database Check

Telegram Excel validation with **CSV-first**, **zero-token rules**, and **Obsidian-like vault memory**.

## Core idea

1. User uploads `.xlsx`
2. System converts to **CSV** (cheaper / cleaner)
3. **Rule engine** fixes most errors with **0 tokens**
4. Only hard rows go to AI (V2 Verifier)
5. Results + learned patterns stored as markdown vault notes (Obsidian style)

GodMode3 multi-model racing is intentionally **not** used (too expensive).

Read: `docs/ARCHITECTURE-CHEAP-SMART.md`

## Quick start

```bash
cp .env.example .env
docker compose up --build -d
```

Services:

- Rule engine (0 token): `http://localhost:8070/health`
- CrewAI fallback: `http://localhost:8080/health`
- Memory API: `http://localhost:8090/health`

Validate:

```bash
curl -X POST http://localhost:8070/rules/validate -F "file=@sample.xlsx"
```

## Obsidian-like vault

```text
vault/
  MEMORY.md
  rules/
  patterns/
  runs/
```

## n8n

Keep your existing **Telegram Database Validator Bot V2**.

Recommended order inside V2:
1. Extract/convert to CSV
2. Call `rule-engine /rules/validate`
3. Send only `ai_needed_rows` to Appointment/Verifier AI
4. Merge corrected CSV + AI fixes
5. Convert final output to XLSX and send on Telegram

Import helpers remain under `n8n-import/`.

## Tests

```bash
python3 -m pip install openpyxl pandas pydantic fastapi
python3 services/tests/test_rule_engine.py
```
