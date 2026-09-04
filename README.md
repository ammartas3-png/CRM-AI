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

## Quality layer (optional, additive)

Semantic routing + Correct-bucket review + conflict matrix — does **not** replace Memory Match.

```bash
bash scripts/fetch_quality_repos.sh   # optional reference clones → third_party/
docker compose up --build -d quality-layer
curl http://localhost:8050/health
python3 scripts/quality_tools.py conflicts
```

Docs: [`docs/QUALITY-LAYER.md`](docs/QUALITY-LAYER.md) · n8n snippets: `n8n-import/snippets/quality-layer-*.js`

## Quick start (local rule-engine)

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8070/health
curl http://localhost:8050/health   # quality-layer
```

## Tests

```bash
python3 -m pip install -r services/rule-engine/requirements.txt -r services/quality-layer/requirements.txt pytest
python3 scripts/validate_rule_system.py
python3 -m pytest -q services/tests
```

## n8n snapshots

Import helpers under `n8n-import/` (Front Door + V2). Live workflows are updated via API on the working branch.
Optional quality-layer ambiguous branch: see `docs/QUALITY-LAYER.md`.
