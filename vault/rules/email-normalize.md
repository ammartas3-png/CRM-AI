---
type: rule
id: email-normalize
priority: 3
token_cost: 0
---

# Email Normalize

## Detect

- Uppercase domains
- Surrounding spaces
- Missing `@`

## Auto-fix

- Trim + lowercase
- Mark missing `@` or `.` as `INVALID_EMAIL`
