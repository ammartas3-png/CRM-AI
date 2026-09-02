# CRM-AI Rule Index

Canonical status rules live here as markdown. **Obsidian is optional** — GitHub or any editor is enough.

Operating manual: [`docs/RULE-CHANGE.md`](../docs/RULE-CHANGE.md)

## Status rules (approved)

- [`currently-busy-is-na`](rules/currently-busy-is-na.md)
- [`invalid-mail-ignored`](rules/invalid-mail-ignored.md)
- [`denied-registration-1x`](rules/denied-registration-1x.md)
- [`call-again-5-na-days`](rules/call-again-5-na-days.md)
- [`money-plus-callback`](rules/money-plus-callback.md)
- [`potential-manual-check`](rules/potential-manual-check.md)
- [`decline-manual-check`](rules/decline-manual-check.md)
- [`recall-to-call-again`](rules/recall-to-call-again.md)
- [`keep-no-potential`](rules/keep-no-potential.md)

## Schema / normalize helpers

- [`required-columns`](rules/required-columns.md)
- [`phone-normalize`](rules/phone-normalize.md)
- [`email-normalize`](rules/email-normalize.md)

## How to change a rule

1. Open a GitHub Issue with the **Rule change** template (or paste the Wrong lead to Cursor)
2. Add/update `vault/rules/<id>.md`
3. Append a golden row in `evals/golden_leads.jsonl`
4. Update `services/rule-engine/crm_classify.py`
5. Run `python3 scripts/validate_rule_system.py` and pytest
6. Sync live n8n **Memory Match**

## Runtime order

1. Zero-token rules (`crm_classify` / Memory Match) — `token_cost: 0`
2. Only unresolved rows → small AI
3. Never treat CrewAI or semantic cache as the primary classifier
