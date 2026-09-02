---
type: pattern
id: duplicate-phone
token_cost: 0
---

# Duplicate Phone Pattern

If the same normalized phone appears more than once:

1. Keep first non-empty name/email row as primary
2. Mark later rows as `DUPLICATE_PHONE`
3. Do not send duplicates to LLM
