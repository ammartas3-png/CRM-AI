# Deploy check (Registration Date Time + Wrong-file fixes)

After importing `05-V2-smart-upgraded.workflow.json` into live n8n:

1. Open **Main Report Filter** code — first columns must be:
   `brand` → `account no` → **`Registration Date Time`** → `customer status`
2. Open **Memory Match** — search for `recall_kept_under_agent_dial_na` (must exist)
3. Open **Apply Verifier Columns** — search for `blocked_bare_reg_not_denied` (must exist)
4. Re-run one small Excel that has a Registration Date column
5. Output Validation XLSX must show **Registration Date Time** as column 3

If column 3 is still `customer status`, the import did **not** update the live workflow (wrong workflow id / draft not activated / old version kept).
