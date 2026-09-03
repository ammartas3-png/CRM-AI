# Golden evals

`golden_leads.jsonl` locks CRM status rules. Each line is one JSON object.

## Required fields

- `account no`
- `customer status`
- `last 10 comments`
- at least one of:
  - `expect_status`
  - `expect_status_family`
  - `expect_validation`
  - `expect_source_contains`
  - `expect_skip_ai`

## Add a case

```bash
python3 scripts/new_rule.py --id my-rule --title "..." --status "Call Again"
# then edit the appended golden line + implement code
python3 -m pytest -q services/tests/test_golden_classify.py
```

See `docs/RULE-CHANGE.md`.

## n8n brain regression sets

The production classifier is the n8n **Memory Match** node, so its rules are tested
directly rather than only through the Python engine:

- `wrong_review_cases.jsonl` — 59 leads a human reviewed one by one from a 1594-lead
  run, each with the status the reviewer decided. Run with `node scripts/mm_harness.js`.
- `appointment_cases.jsonl` — leads where the appointment AI found a callback that must
  NOT reopen the lead (stale, bogus time, or refusal-locked).
  Run with `node scripts/appt_harness.js`.
- `rules_sheet.json` — snapshot of the live Google Sheet rule rows the node reads, so the
  harness sees the same base statuses as production.

Both harnesses run in CI. Edit the node with `scripts/node_code.py extract|inject`.
