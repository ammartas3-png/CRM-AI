---
id: call-again-vs-recall-vs-np
token_cost: 0
---

# Call Again vs Recall vs No Potential

Status decision tree for the three most-confused families (conflict report top rows).

## Call Again
- Soft money with a near-term funding plan (salary soon, arrange funds, ask friends, will bring then continue)
- Real customer callback / busy-after-pickup / concrete time
- CRM Call Again / Recall kept under 5 distinct NA days when nothing harder applies

## Recall
- Single refusal / non-cooperative day (playing around, dont want + hu, leave it)
- Agent dial notes (`cb:vm`, `cb na`, `call again rej`) are **not** customer callbacks — leftover refusal stays Recall
- No Interest needs **two** refusal-level days; one day is Recall only

## No Potential
- Hard money / dead funding (by October, in 4 months, months to save, no job, not serious, reply when ready)
- Money close (`capital affordable? no + hu`)
- Money + discontinue / cancel without a funding plan (`policy:money_quit`)
- Phone unreachable / email-only

## Priority (newest meaningful comment)
1. Language barrier → No Language
2. Hard money / money+quit → No Potential
3. Soft money + funding plan → Call Again
4. Newest refusal (after stripping agent dial) → Recall / No Interest
5. Real customer arrange → Call Again
6. Keep CRM Call Again / Recall / NA under streak rules
