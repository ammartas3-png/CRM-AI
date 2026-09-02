---
type: rule
id: phone-normalize
priority: 2
token_cost: 0
---

# Phone Normalize

## Detect

- Spaces, dashes, parentheses
- Leading `00` instead of `+`
- TR local format starting with `0`

## Auto-fix

- Keep digits and leading `+`
- If starts with `0` and length is 11 (TR mobile), convert to `+90...`
- If starts with `00`, convert to `+`
- Flag rows that remain < 10 digits as `INVALID_PHONE`
