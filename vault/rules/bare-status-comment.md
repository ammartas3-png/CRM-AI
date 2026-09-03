---
id: bare-status-comment
token_cost: 0
---

# A comment that is only a status label is not evidence

Agents paste the CRM status into the comment field (`No potential;`, `Call Again;`,
`Denied Registration;`). A line whose entire content is a status name carries no
customer information, so it is treated as a system line and never matched by keyword
rules. `na` and `no answer` are excluded from this: those are real dialer outcomes.
