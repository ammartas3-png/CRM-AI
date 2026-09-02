# Smart upgrades applied to V2

Live n8n workflow `Telegram Database Validator Bot V2` now includes:

1. CSV/XLSX/XLS/JSON extract path (File Kind Switch)
2. Telegram Front Door workflow for `/start` + file upload
3. Cheaper AI batches (short comments, batch=15)
4. Instructor-like JSON repair after AI Agent
5. Stricter Verifier gate (skip deterministic Correct / no-answer)
6. Models switched to `gpt-5.4-mini`
7. Stronger prompt-injection resistant system prompt
8. Confidence / Auto Accept enrichment (Smart Trace)
9. Telegram summary message before XLSX reports
10. Decision Memory Logger + Google Sheets `Decision_Memory` append
11. Rule Hit Tracker in workflow staticData
12. Slim main Excel report (34 → 16 columns): drops internal/AI-debug fields; adds **Match Detail**

### Main report columns (kept)

`brand`, `account no`, `customer status`, `Suggested Status`, `Validation Result`, `Reason`, `Decision Source`, **`Match Detail`**, `Confidence`, `Review Priority`, `Injection Flag`, `When To Call`, `Agent`, `country`, `Current Agent Office`, `last 10 comments`

**Match Detail** examples:
- `Row 65: call after (after 4 pm)` — Google Sheet rule satırı + tetikleyici + eşleşen kelime
- `Row 405: rej (streak days=1)` — sheet kuralı
- `Policy: no_real_conversation | trigger: na | streak days=0` — sheet satırı yoksa politika kaynağı

### Dropped from main report (still computed internally)

`memory_matched`, `skipAI`, `matched_trigger`, `Matched Sheet Row`, `Matched Keyword`, appointment debug fields, `Rule Hit Count`, all `AI Check*` / verifier debug columns, `Confidence Score` / `Confidence Reason`, `Auto Accept`

Manual Entry and 5UP files were already slim and are unchanged.

## Supporting GitHub-inspired layers in repo

- `vault/` Obsidian-like markdown memory
- `services/rule-engine` zero-token fixes
- `services/smart-layer` Pandera + Instructor helpers
- `services/memory-service` MCP-compatible graph memory

## Important Google Sheet setup

Create a tab named exactly `Decision_Memory` in spreadsheet `CRM_AI_Rules`.
If missing, append node continues without failing the run.

## Accuracy fixes (2026-09-02)

Applied after reviewing execution #1114 input vs output:

1. **Canonical status compare** — `No Potential - no documents` ≡ `No Potential` (stops false Wrong + Manual Entry noise)
2. **Keep sheet subtype on no_money** — preserve `No Potential - no documents` instead of collapsing
3. **Merge continuation comment lines** — multiline bodies keep timestamp so `cb tmrw` stays with the talk
4. **busy_after_pickup** — `pu ... busy/lm` is Call Again, not `no_real_conversation`
5. **Stale callback then NA** — newer `rej`/`navm` overrides older Call Again
6. **Appointment timestamp false positives** — reject metadata dates as `When To Call`
7. **AI prompts** — money+concrete callback → Call Again; Appointment AI anti-false-positive rules
