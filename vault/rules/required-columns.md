---
type: rule
id: required-columns
priority: 1
token_cost: 0
---

# Required Columns

Every database file must include these columns (case-insensitive aliases allowed):

- `name` / `ad` / `customer_name`
- `phone` / `telefon` / `mobile`
- `email` / `mail`

## Auto-fix

- Rename aliases to canonical names: `name`, `phone`, `email`
- Trim whitespace
- Drop completely empty rows
