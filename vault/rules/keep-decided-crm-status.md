---
id: keep-decided-crm-status
token_cost: 0
---

# Keep a decided CRM outcome when nothing contradicts it

When the CRM already carries a decided outcome (`No Potential`, `No Interest`,
`Denied Registration`, `Wrong Number or Email`, `No Language`, `Invalid country`,
`Under 18`) and no policy signal contradicts it, that status is kept instead of being
replaced by a no-answer fallback or handed to the AI.

Exception: a CRM `No Potential` lead whose log still shows an open callback and no
money statement goes back to **Call Again** — it was never actually disqualified.
