# Deploy check (Registration Date Time + Wrong-file fixes)

After importing `05-V2-smart-upgraded.workflow.json` into live n8n:

1. Open **Main Report Filter** code — first columns must be:
   `brand` → `account no` → **`Registration Date Time`** → `customer status`
2. Open **Memory Match** — search for `recall_kept_under_agent_dial_na` (must exist)
3. Open **Apply Verifier Columns** — search for `blocked_bare_reg_not_denied` (must exist)
4. Re-run one small Excel that has a Registration Date column
5. Output Validation XLSX must show **Registration Date Time** as column 3

If column 3 is still `customer status`, the import did **not** update the live workflow (wrong workflow id / draft not activated / old version kept).

## Sheet sync (no por / urdu-hindi / mistake) — 2026-09-11

n8n **Get row(s) in sheet** reads live Google Sheet `17m6No_sKILzLs5ZjmND0FykwkjFBLvWhiJP6NCcKq8E`.
Policy in Memory Match already covers these cases, but sheet triggers must stay aligned.

Paste / apply from repo:
- `evals/SHEET_UPDATES_NO_POR_LANG_MISTAKE.csv` (this batch)
- `evals/SHEET_UPDATES_ACC_WRONG_FILE.csv` (earlier bare-reg + interested=false)

Critical:
1. Row **290** `no documents or bank account` → **No Potential** (not Invalid Country); first/repeat = No Potential - no documents
2. **ADD** `doesnt have por` / `don't have por` / `no proof of residence` → No Potential - no documents
3. **ADD** `urdu speaker` / `hindi speaker` / `indian speaker` / `speaks urdu|hindi` → **Call Again**
4. **ADD** `signed up by mistake` → Recall (day1) / No Interest (repeat day)
5. Rows 464/465/468/477 when_not: Urdu/Hindi desk → Call Again transfer
6. Confirm row **112** `interested` stays **active=FALSE**
7. Repo mirror: `evals/rules_sheet.json` (710 rows after sync)

Service account cannot write the live sheet (403) — owner must paste CSV or share edit access.
