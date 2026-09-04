# Rule Engine + Vault → V2 Integration

## Single rule source

| Layer | Role |
|------|------|
| `services/rule-engine/crm_classify.py` + `vault/` | **Canonical** zero-token business rules |
| `evals/golden_leads.jsonl` + CI | Regression lock |
| Live n8n **Memory Match** | Production mirror (n8n cloud cannot call localhost) |
| Exact fingerprint cache | Safe reuse of skipAI decisions (not semantic) |

**How to change rules day-to-day:** [`docs/RULE-CHANGE.md`](RULE-CHANGE.md)  
Issue template: `.github/ISSUE_TEMPLATE/rule-change.yml` · scaffold: `scripts/new_rule.py`

Do **not** add CrewAI or semantic cache as the main engine. Obsidian is optional; GitHub markdown is enough.

## Status

| Piece | Status |
|------|--------|
| `POST /rules/classify-leads` | Implemented (+ Pandera gate + exact cache) |
| Vault run/decision notes | Implemented |
| Golden set + GitHub Actions CI | `evals/` + `.github/workflows/ci.yml` |
| Live n8n Memory Match | Synced with approved rules + sheet governance |
| Front Door → V2 `chat_id` | Live (multipart form field) |
| Dynamic Telegram chatId | Live (workflow staticData) |
| HTTP Shadow node in n8n cloud | Ready when `RULE_ENGINE_URL` is public |

## Approved rules (owner answers)

1. `currently busy` (no talk) → **No Answer 1-5**
2. `invalid mail` + phone NA → **No Answer** (mail does not change status)
3. First wrong number → **Denied Registration**
4. Call Again → No Answer only after **5 distinct NA days**
5. `no money` + concrete callback → **Call Again**
6. CRM `Potential` → **Manual Check**
7. `Decline` → **Manual Check** (never auto-change)
8. Recall + newer callback → **Call Again**

## Run rule-engine locally

```bash
docker compose up -d --build rule-engine
curl http://127.0.0.1:8070/health
curl -X POST http://127.0.0.1:8070/rules/classify-leads \
  -H 'Content-Type: application/json' \
  -d '{"leads":[{"account no":"ACC1","customer status":"Call Again","last 10 comments":"2026-09-02 10:00 | X | na;"}],"write_vault":true}'
```

## Shadow phase (when public URL exists)

1. Host rule-engine (Railway/Fly/VPS) with vault volume
2. In V2 after Normalize / before AI:
   - HTTP Request → `{{$env.RULE_ENGINE_URL}}/rules/classify-leads`
   - Body: `{ "leads": <normalized leads>, "source": "n8n-v2-shadow" }`
3. Optionally add columns `Engine Suggestion` / `Engine Source` for comparison
4. When agreement is high, set gate: `skipAI=true` rows use engine decision

## Sheet governance

Memory Match skips Google Sheet rows that look AI-generated (`source`/`keyword_group`/`ai_generated`) unless `human_approved` / `reviewed` / `approved` is true. Prefer editing `crm_classify.py` + golden cases over dumping aggressive sheet phrases.

## Not in this phase

- CrewAI as primary classifier
- Semantic (embedding) cache as primary cache
- memory-service graph
