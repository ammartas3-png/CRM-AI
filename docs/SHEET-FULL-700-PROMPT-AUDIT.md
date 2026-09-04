# Full sheet audit vs AI Agent prompt (700/700)

Date: 2026-09-04  
Gantry: AI Agent system prompt + vault money/callback/refusal tree  
Source snapshot: `evals/rules_sheet.json`

## Method

Every row (700) was checked programmatically for:
1. Status ∈ AI prompt vocabulary
2. Over-broad / bare status / dialer-only triggers
3. Money → status conflicts (soft/hard/plan/callback)
4. Refusal → Call Again conflicts
5. when_to_use vs suggested_status contradictions
6. Unreviewed `ai_output` high-risk rules

## Result

| | Count |
|---|---:|
| Rows audited | **700** |
| Issues found | **44** |
| P0 | 13 |
| P1 | 28 |
| P2 | 3 |
| Clean (no flag) | **656** |

**Yes — errors were found** (44). Not a free-for-all: most sheet rows (656) are consistent with the prompt gantry.

## P0 (must-fix)

- Row 124 `no money for now` → `Call Again` — `money_to_ca_without_plan`: money-ish → Call Again without funding plan/callback guard: 'no money for now'
- Row 130 `call again` → `Call Again` — `bare_status_paste`: trigger is bare CRM status label: 'call again'
- Row 172 `asked for call today` → `Call Again` — `money_to_ca_without_plan`: money-ish → Call Again without funding plan/callback guard: 'asked for call today'
- Row 233 `wrong number` → `Wrong Number or Email` — `bare_status_paste`: trigger is bare CRM status label: 'wrong number'
- Row 366 `no answer` → `No Answer 1-5` — `bare_status_paste`: trigger is bare CRM status label: 'no answer'
- Row 402 `dvm` → `No Answer 1-5` — `too_short`: trigger too short: 'dvm'
- Row 404 `ndt` → `No Answer 1-5` — `too_short`: trigger too short: 'ndt'
- Row 405 `rej` → `No Answer 1-5` — `too_short`: trigger too short: 'rej'
- Row 406 `db` → `No Answer 1-5` — `too_short`: trigger too short: 'db'
- Row 407 `na` → `No Answer 1-5` — `too_short`: trigger too short: 'na'
- Row 408 `vm` → `No Answer 1-5` — `too_short`: trigger too short: 'vm'
- Row 422 `no answer 1-5` → `No Answer 1-5` — `bare_status_paste`: trigger is bare CRM status label: 'no answer 1-5'
- Row 684 `under 18` → `Under 18` — `bare_status_paste`: trigger is bare CRM status label: 'under 18'

## P1

- Row 124 `no money for now` → `Call Again` — `unreviewed_ai_rule`
- Row 147 `wanted to know his sc` → `Call Again` — `when_refusal_for_ca`
- Row 165 `cb at am for deposit` → `Call Again` — `when_refusal_for_ca`
- Row 200 `not now` → `Call Again` — `unreviewed_ai_rule`
- Row 205 `i will give it a pass` → `Call Again` — `when_refusal_for_ca`
- Row 251 `fake` → `Denied Registration` — `weak_identity_trigger`
- Row 379 `ringing` → `No Answer 1-5` — `dialer_token`
- Row 390 `pu hu` → `No Answer 1-5` — `dialer_token`
- Row 397 `busy` → `No Answer 1-5` — `dialer_token`
- Row 398 `cnbr` → `No Answer 1-5` — `dialer_token`
- Row 400 `navm` → `No Answer 1-5` — `dialer_token`
- Row 402 `dvm` → `No Answer 1-5` — `dialer_token`
- Row 404 `ndt` → `No Answer 1-5` — `dialer_token`
- Row 405 `rej` → `No Answer 1-5` — `dialer_token`
- Row 406 `db` → `No Answer 1-5` — `dialer_token`
- Row 407 `na` → `No Answer 1-5` — `dialer_token`
- Row 408 `vm` → `No Answer 1-5` — `dialer_token`
- Row 543 `am broke and` → `No Potential` — `unreviewed_ai_rule`
- Row 562 `leave leave it` → `Recall` — `unreviewed_ai_rule`
- Row 565 `you have to cancel it` → `Recall` — `unreviewed_ai_rule`
- Row 638 `cancel it pls` → `Recall` — `unreviewed_ai_rule`
- Row 640 `dont want` → `Recall` — `unreviewed_ai_rule`
- Row 643 `doesnt want to follow` → `Recall` — `unreviewed_ai_rule`
- Row 653 `saw scam website` → `Recall` — `unreviewed_ai_rule`
- Row 660 `said cancel` → `Recall` — `unreviewed_ai_rule`
- Row 674 `im already cancel cancel` → `Recall` — `unreviewed_ai_rule`
- Row 700 `No Por` → `No Potential - no documents` — `unreviewed_ai_rule`
- Row 701 `cb tmrw` → `Call Again` — `unreviewed_ai_rule`

## P2

- Row 473 `malayalam` → `No Language` — `weak_language_token`
- Row 474 `kannada` → `No Language` — `weak_language_token`
- Row 475 `telugu` → `No Language` — `weak_language_token`

## Patches applied in repo (this pass)

- Row 205: `i will give it a pass` status Call Again→Recall active=True — refusal language → Recall not CA
- Row 251: `fake` status Denied Registration→Recall active=True — fake+when mismatch: first refusal is Recall not Denied Registration
- Row 422: `no answer 1-5` status No Answer 1-5→No Answer 1-5 active=False — deactivate bare status paste no answer 1-5
- Row 147: `wanted to know his sc` status Call Again→Call Again active=True — SC ask can be CA; block hard refuse
- Row 165: `cb at am for deposit` status Call Again→Call Again active=True — deposit CB vs cancel
- Row 172: `asked for call today` status Call Again→Call Again active=True — no funds + asked call today = CA only with customer callback
- Row 124: `no money for now` status Call Again→Call Again active=True — confirm soft money CA only with callback
- Row 233: `wrong number` status Wrong Number or Email→Wrong Number or Email active=True — wrong number phrase OK; guard agent paste
- Row 366: `no answer` status No Answer 1-5→No Answer 1-5 active=True — no answer phrase OK as dialer/hangup evidence
- Row 684: `under 18` status Under 18→Under 18 active=True — under 18 OK with explicit age
- Row 402: `dvm` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for dvm
- Row 404: `ndt` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for ndt
- Row 405: `rej` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for rej
- Row 406: `db` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for db
- Row 407: `na` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for na
- Row 408: `vm` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for vm
- Row 379: `ringing` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for ringing
- Row 390: `pu hu` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for pu hu
- Row 397: `busy` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for busy
- Row 398: `cnbr` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for cnbr
- Row 400: `navm` status No Answer 1-5→No Answer 1-5 active=True — dialer-only guard for navm
- Row 543: `am broke and` status No Potential→No Potential active=True — broke → NP ok with plan guard
- Row 200: `not now` status Call Again→Call Again active=True — not now soft defer CA
- Row 700: `no por` status No Potential - no documents→No Potential active=True — No Por = no proof of residence / docs
- Row 701: `cb tmrw` status Call Again→Call Again active=True — cb tmrw OK customer callback
- Row 562: `leave leave it` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 565: `you have to cancel it` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 638: `cancel it pls` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 640: `dont want` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 643: `doesnt want to follow` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 653: `saw scam website` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 660: `said cancel` status Recall→Recall active=True — refusal/cancel first day = Recall
- Row 674: `im already cancel cancel` status Recall→Recall active=True — refusal/cancel first day = Recall

## Notes

- Dialer tokens (`na`,`vm`,`rej`,…) are **kept** for No Answer streak evidence but guarded so they cannot justify Wrong Number / CA / NP.
- Bare `call again` already inactive from prior audit.
- Live Google Sheet must copy these `evals/rules_sheet.json` edits.
- Machine-readable dump: `evals/sheet_prompt_audit.json`

## Re-test

```bash
node scripts/mm_harness.js   # expect 61/61
```
