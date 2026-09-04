---
id: agent-dial-notes
token_cost: 0
---

# Agent dial notes are not a customer callback

Agents log their own dialing in the comment field: `cb : vm`, `cb na x2`, `cb rej`,
`CALLED BACK PUHU`, `call again rej`, `when i tried to cb she rejected`,
`I said I would hang up and call back`.

None of this is the customer asking to be called back, so these phrases are stripped
before callback, busy-after-pickup and refusal detection run. What remains decides the
status: usually the CRM value (`No Answer 1-5`, `Recall`) rather than `Call Again`.
