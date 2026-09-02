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
5. **Call Again → No Answer only after 5 distinct NA days** — 1–4 days of `rej`/`navm` do NOT wipe Call Again (`call_again_kept_under_5na` / `call_again_5na_days`)
6. **Sheet guards** — Google Sheet rules no longer override policies: skip `no_answer` rows while CRM Call Again protected (<5 NA days); skip `busy` on pickup lines; skip row 130 when agent pasted `Call Again` status
7. **Appointment timestamp false positives** — reject metadata dates as `When To Call`
8. **AI prompts** — money+concrete callback → Call Again; Appointment AI anti-false-positive rules

Sheet'i elle düzenlemeniz gerekmez; motor çakışan satırları kodda yok sayar. İsteğe bağlı: row 397/405/407/130 yukarıdaki gibi korunur.

## Chunking (large files)

- Soft limit raised to **2500 leads per run** so typical CRM exports (~1800) send **one** Telegram report set.
- If still over 2500: sequential chunks continue, but remaining queue is passed in the webhook body (fixes a race that dropped parts 3/4 after 500+500).

See also: `docs/RULE-ENGINE-INTEGRATION.md` (classify-leads + vault + live Memory Match sync of approved rules).

## Director upgrades (2026-09-02)

Implemented without CrewAI / semantic-cache as primary engine:

1. **Single rule source** — `crm_classify.py` + vault canonical; Memory Match is the live mirror; golden set locks behavior
2. **Golden set + CI** — `evals/golden_leads.jsonl`, `.github/workflows/ci.yml`
3. **Front Door in git** — `n8n-import/06-Front-Door-Telegram.workflow.json`
4. **Dynamic Telegram chatId** — Front Door sends `chat_id` form field; V2 stores `staticData.telegramChatId` and all Telegram send nodes use it
5. **Webhook env fallback** — Chunk Router / Schedule Next Chunk read `N8N_WEBHOOK_DATABASE_CHECK` or `DATABASE_CHECK_WEBHOOK_URL`
6. **Sheet governance** — unapproved `ai_generated` sheet rows are skipped in Memory Match
7. **Manual Entry closed loop** — columns `Applied to CRM`, `Applied At`, `Applied By`, `Review Notes`
8. **Agent score** — Telegram summary lists per-agent correct %
9. **Pandera gate + exact cache** — rule-engine classify path (`lead_gate.py`, `exact_cache.py`)
