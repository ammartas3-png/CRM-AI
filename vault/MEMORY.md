# CRM-AI Memory Index

This vault works like Obsidian:

- `[[required-columns]]`
- `[[phone-normalize]]`
- `[[email-normalize]]`
- `[[duplicate-phone]]`

## How agents should use it

1. Load rules from `vault/rules/`
2. Apply all `token_cost: 0` fixes first
3. Only if unresolved issues remain, call a small LLM
4. Write each run into `vault/runs/`
