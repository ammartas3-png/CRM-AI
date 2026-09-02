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
