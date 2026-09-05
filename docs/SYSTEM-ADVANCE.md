# System advance (zero local installs)

This pass upgrades CRM-AI using patterns from high-star repos **without** requiring
FreeLLMAPI / Ollama / OpenHuman on your PC.

## What landed

| Layer | Inspiration | Repo artifact |
|---|---|---|
| Structured AI JSON gate | Instructor / Outlines | `services/quality-layer/structured_out.py` + `/quality/validate-ai-batch` |
| Semantic example bank | semantic-router + sentence-transformers | `services/quality-layer/semantic_bank.py` + `/quality/semantic-route` |
| Cascade stage | support-ticket-classifier | `cascade.py` → `rules→fuzzy→semantic→ml→llm-flag` |
| Prompt gantry eval | promptfoo | `scripts/ai_prompt_eval.js` + `evals/ai_prompt_fixtures.jsonl` |
| Sheet↔prompt audit | Great Expectations / Evidently | `scripts/sheet_prompt_audit.py` |
| Memory Match | vault money/callback tree | soft-money plan override, agent-dial keep-CA block, hangup→Recall keep |
| Sheet P0 | bare status paste | rows 233 / 366 / 684 deactivated in `evals/rules_sheet.json` |
| AI / Verifier prompts | Instructor contract | ALLOWED status list + structured output contract in V2 JSON |
| CI | — | prompt eval + sheet audit + quality advance tests |

## What you still do once (no new software)

1. Re-import `n8n-import/05-V2-smart-upgraded.workflow.json` (and Front Door if survey wiring changed).
2. Mirror deactivated sheet rows **233, 366, 684** on the live Google Sheet.
3. Optional: set `QUALITY_LAYER_URL` if you already run the quality-layer container.

## Verify

```bash
node scripts/mm_harness.js          # expect 66/66
node scripts/ai_prompt_eval.js
python3 scripts/sheet_prompt_audit.py
python3 -m pytest -q services/tests/test_quality_layer.py services/tests/test_quality_advance.py
```
