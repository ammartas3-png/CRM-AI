# CRM-AI — Cheap + Smart Database Check

Telegram Excel validation with **CSV-first**, **zero-token rules**, and a **repo + golden + n8n** rule system.

## Production path (live today)

1. Telegram → Front Door → V2 webhook (`Database-check`)
2. Memory Match applies approved status rules (0 token)
3. Only hard rows go to small AI
4. Summary + XLSX reports back to Telegram

## Rule management (no Obsidian required)

```text
Issue (Wrong lead) → vault/rules → golden_leads.jsonl → crm_classify.py → CI → n8n Memory Match
```

- Manual: [`docs/RULE-CHANGE.md`](docs/RULE-CHANGE.md)
- Index: [`vault/MEMORY.md`](vault/MEMORY.md)
- Scaffold: `python3 scripts/new_rule.py --id ... --title ... --status ...`
- Validate: `python3 scripts/validate_rule_system.py`

GodMode3 multi-model racing is intentionally **not** used (too expensive).

Also read: `docs/ARCHITECTURE-CHEAP-SMART.md`, `docs/RULE-ENGINE-INTEGRATION.md`

## Quick start (local rule-engine)

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8070/health
```

## Tests

```bash
python3 -m pip install -r services/rule-engine/requirements.txt pytest
python3 scripts/validate_rule_system.py
python3 -m pytest -q services/tests
```

## n8n snapshots

Import helpers under `n8n-import/` (Front Door + V2). Live workflows are updated via API on the working branch.
