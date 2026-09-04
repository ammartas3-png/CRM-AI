# Sheet fixes from Correct-audit (~61 high-signal)

Date: 2026-09-04  
Source audit: Correct bucket suspects where engine==CRM but comments contradict (`/tmp/correct_audit.json`).

## Decision summary

High-signal families (~42–61 leads):
- Call Again + money block, no funding plan
- Call Again + only agent redial `cb`
- Call Again + newest refusal
- Soft temporary money should be Recall / hard money No Potential
- Broad sheet triggers (`interested`, `call again`, `call back`) rubber-stamped status

Root cause mix:
1. **Sheet** over-broad triggers
2. **Memory Match** treated bare `cb` / bare `next week` as customer callback and overrode sheet money/refusal rows

## Repo changes already applied

1. `evals/rules_sheet.json` — 26 row edits (this file lists them)
2. `n8n-import/05-V2-smart-upgraded.workflow.json` Memory Match:
   - Removed bare `cb|cbk|clbk|cback` from `ARRANGE_RE`
   - `hasArrangeIn` requires a real arrange phrase (weekday alone ≠ callback)
   - Newest hard money without funding plan / concrete customer callback no longer loses to weak `callback_in_newest`

## Live Google Sheet actions

Apply these to the live `CRM_AI_Rules` tab (match `evals/rules_sheet.json`):

- **Row 112** `interested`: status `Call Again`→`Call Again`, active=False — Deactivate bare interested → CA
- **Row 130** `call again`: status `Call Again`→`Call Again`, active=False — Deactivate bare call again
- **Row 136** `call back`: status `Call Again`→`Call Again`, active=False — Deactivate bare call back
- **Row 129** `call me back`: status `Call Again`→`Call Again`, active=True — Tighten call me back
- **Row 43** `call next week`: status `Call Again`→`Call Again`, active=True — Tighten call next week
- **Row 40** `said he is busy`: status `Call Again`→`Call Again`, active=True — Busy vs refusal guard
- **Row 50** `call me after`: status `Call Again`→`Call Again`, active=True — call me after vs refusal
- **Row 134** `make his deposit`: status `Call Again`→`Call Again`, active=True — make his deposit guard
- **Row 527** `cant afford`: status `No Potential`→`No Potential`, active=True — cant afford
- **Row 528** `not afford`: status `No Potential`→`No Potential`, active=True — not afford
- **Row 521** `do not have funds`: status `No Potential`→`No Potential`, active=True — do not have funds
- **Row 574** `dont have money now`: status `Recall`→`Recall`, active=True — dont have money now
- **Row 571** `money not available now`: status `Recall`→`Recall`, active=True — temporary money family
- **Row 572** `no money to deposit now`: status `Recall`→`Recall`, active=True — temporary money family
- **Row 573** `do not have money now`: status `Recall`→`Recall`, active=True — temporary money family
- **Row 577** `no funds now`: status `Recall`→`Recall`, active=True — temporary money family
- **Row 578** `no money now`: status `Recall`→`Recall`, active=True — temporary money family
- **Row 616** `dont want to do it`: status `Recall`→`Recall`, active=True — dont want vs weak time
- **Row 626** `not interested`: status `Recall`→`Recall`, active=True — not interested
- **Row 621** `not comfortable`: status `Recall`→`Recall`, active=True — not comfortable
- **Row 632** `skeptical`: status `Recall`→`Recall`, active=True — skeptical
- **Row 476** `tamil`: status `No Language`→`No Language`, active=True — tamil
- **Row 249** `denied the registration`: status `Denied Registration`→`Denied Registration`, active=True — denied the registration
- **Row 251** `fake`: status `Denied Registration`→`Denied Registration`, active=True — fake
- **Row 402** `dvm`: status `No Answer 1-5`→`No Answer 1-5`, active=True — dvm
- **Row 406** `db`: status `No Answer 1-5`→`No Answer 1-5`, active=True — db

### Deactivate immediately (highest risk)
- Row 112 `interested`
- Row 130 `call again`
- Row 136 `call back`

### Keep but tighten when_not_to_use
- Finance NP rows 521/527/528
- Temporary money Recall rows 571–578 / 574
- Refusal Recall rows 616/621/626/632

## Re-test

```bash
node /tmp/audit_correct.js
```

Expect drops especially in:
- Call Again + money block
- Call Again + agent redial
- Call Again + refusal


## Re-test results (after repo fixes)

| Metric | Before | After |
|---|---:|---:|
| Correct bucket | 1435 | 1407 |
| Suspicious Correct | 144 | 129 |
| CA + money no plan | 16 | 2 |
| CA + refusal newest | 7 | 5 |
| CA + agent redial only | 15 | 14 |

Remaining ~14 agent-redial Corrects are mostly CRM Call Again kept under 5 NA with no harder signal — by design for streak keep; they need human Telegram review, not more sheet deactivation.

Remaining ~60 No Potential without money text / ~32 wrong-number without claim are mostly `crm_decided_kept` (CRM already that status, no contradicting signal). Separate review queue — not sheet phrase bugs.
