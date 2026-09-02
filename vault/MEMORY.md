# CRM-AI Memory Index

This vault works like Obsidian:

- `[[required-columns]]`
- `[[phone-normalize]]`
- `[[email-normalize]]`
- `[[duplicate-phone]]`
- `[[currently-busy-is-na]]`
- `[[invalid-mail-ignored]]`
- `[[call-again-5-na-days]]`
- `[[money-plus-callback]]`
- `[[potential-manual-check]]`

## How agents should use it

1. Load rules from `vault/rules/` (canonical with `services/rule-engine/crm_classify.py`)
2. Apply all `token_cost: 0` fixes first (`rule-engine /rules/classify-leads` + exact cache)
3. Only if unresolved issues remain, call V2 Memory Match / small LLM
4. Write each run into `vault/runs/` and decisions into `vault/decisions/`
5. Never treat CrewAI or semantic cache as the primary classifier
6. Lock behavior with `evals/golden_leads.jsonl` before changing rules
