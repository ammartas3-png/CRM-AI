# AI Prompt ↔ Google Sheet semantic alignment

Date: 2026-09-04  
Canonical source: `vault/rules/call-again-vs-recall-vs-np.md`, `vault/rules/money-plus-callback.md`, `vault/rules/money-with-funding-plan.md`

## Verdict

Yes — **semantic conflicts existed**, mainly in the money / callback / refusal family (also the top rows in `evals/conflict_report.json`).

Runtime still avoids double-firing (sheet/Memory Match hit → `skipAI=true`), but when Memory Match missed and AI ran, the **prompt tree disagreed with sheet+vault**.

## Canonical tree (now shared)

1. Language barrier → **No Language**
2. Hard money / money+quit / distant funding → **No Potential**
3. Soft money + near-term funding plan **OR** concrete **customer** callback → **Call Again**
4. Newest customer refusal (strip agent dial notes) → **Recall** (1 day) / **No Interest** (2+ days)
5. First soft temporary “no money now” (open, no plan, no hard refusal) → **Recall**
6. Real customer arrange / busy-after-pickup → **Call Again**
7. Keep CRM Call Again / Recall / No Answer under 5 distinct NA-day streak rules

Agent dial notes alone (`cb:vm`, `cb na`, `call again rej`, “I will hang up and call back”) are **not** customer callbacks.

## Conflicts found

| Area | AI prompt (before) | Sheet / Memory Match | Canonical fix |
|---|---|---|---|
| Bare no money, no callback | **No Potential** | Often **Call Again** or **Recall** | Split: hard→NP, soft temporary→Recall, plan/callback→CA |
| Soft money + salary/arrange plan | Collapsed into NP | Sheet often **Call Again** | **Call Again** |
| Money + concrete customer CB | Call Again | Call Again | Keep (aligned) |
| Meaningful talk + any money (MM) | — | Forced **Recall** | Use money family helper (CA/NP/Recall) |
| Agent dial “cb” noise | Weak | Over-triggered Call Again | Explicitly excluded from customer callback |
| “doesn't have money” + no job (sheet row 164) | NP | **Call Again** | Sheet → **No Potential** |
| “am broke” (row 543) | NP | **Recall** | Sheet → **No Potential** |
| Deposit page + temporary no money (row 176) | NP/Recall | **Call Again** | Sheet → **Recall** |

## Code / data changes in repo

1. **AI Agent system prompt** (`n8n-import/05-V2-smart-upgraded.workflow.json`)
   - Added canonical tree
   - Rewrote NO POTENTIAL / CALL AGAIN money rules
   - Rewrote priority rule 5
2. **Memory Match** (same workflow)
   - Replaced `hasMoneyIssue ? Recall : Call Again`
   - Added `moneyFamilyStatus()` + funding/callback/hard/soft helpers
3. **`evals/rules_sheet.json`**
   - Patched conflicting money rows (see list below) with `correction_source=prompt_sheet_align_2026-09-04`

## Google Sheet actions (apply to live `CRM_AI_Rules`)

Update these rows in the live sheet to match `evals/rules_sheet.json`:

- **Row 164** `doesn't have money`: `Call Again` → `No Potential` — AI/sheet conflict: bare no money + no job was Call Again; vault hard money → No Potential
- **Row 571** `money not available now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 572** `no money to deposit now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 573** `do not have money now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 574** `dont have money now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 577** `no funds now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 578** `no money now`: `Recall` → `Recall` — Align temporary money with vault tree
- **Row 124** `no money for now`: `Call Again` → `Call Again` — Keep CA only with customer callback
- **Row 176** `did not currently have the money`: `Call Again` → `Recall` — Deposit-page temporary money without plan → Recall not CA
- **Row 641** `i don't have money`: `Recall` → `Recall` — Clarify soft vs hard
- **Row 503** `had less funds`: `No Potential` → `No Potential` — NP kept; guard for soft arrange
- **Row 543** `am broke and`: `Recall` → `No Potential` — broke without plan → NP not Recall

Also add/confirm `when_not_to_use` guards on all finance triggers:
- funding plan / customer callback → Call Again
- hard permanent / distant / quit → No Potential
- first soft temporary open → Recall

Unapproved `ai_output` finance rows should stay inactive until `human_approved=true` (existing Memory Match governance).

## What was NOT a conflict

- Status vocabulary (Call Again / Recall / No Potential / No Answer 1-5 / No Answer 5 UP) — same families; `Code in JavaScript1` canon normalizes casing/aliases
- Decline / Duplicate / DNC → Manual Check — prompt and vault agree
- Denied Registration 1st day / Wrong Number on repeat — agree
- No Interest needs 2 refusal days — agree

## Re-import

Re-import `n8n-import/05-V2-smart-upgraded.workflow.json` into n8n Cloud after merging.
Then paste sheet row edits into Google Sheets (or replace from `evals/rules_sheet.json`).
