# Rule Engine + Vault → V2 Integration

## Status

| Piece | Status |
|------|--------|
| `POST /rules/classify-leads` | Implemented (8 approved business rules) |
| Vault run/decision notes | Implemented |
| Unit tests | `services/tests/test_crm_classify.py` |
| Live n8n Memory Match | **Updated now** with same 8 rules (so Telegram benefits immediately) |
| HTTP Shadow node in n8n cloud | Ready when `RULE_ENGINE_URL` is public |

## Why Memory Match was updated too

n8n cloud cannot call `localhost:8070`. Until rule-engine is hosted publicly, the approved rules are enforced inside **Memory Match** so production stays correct.

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

## Not in this phase

- CrewAI
- smart-layer Pandera full gate
- memory-service graph
