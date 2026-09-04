# Quality Layer

Adds measurement + ambiguous-lead routing **without rewriting** Memory Match.

## What was added

| Piece | Role | Upstream inspiration |
|---|---|---|
| `services/quality-layer` | FastAPI on `:8050` | — |
| RapidFuzz example-bank router | soft money / agent cb / refusal / language | [semantic-router](https://github.com/aurelio-labs/semantic-router) |
| Correct-bucket review queue + Argilla export | catch "Correct but wrong" | [argilla](https://github.com/argilla-io/argilla), [eval-loop](https://github.com/erinozolins/eval-loop) |
| Conflict matrix | engine↔human disagreements by family | [snorkel](https://github.com/snorkel-team/snorkel) |
| n8n snippets | optional ambiguous branch | — |

## Run locally

```bash
docker compose up -d --build quality-layer
curl http://127.0.0.1:8050/health

# conflict report from golden + wrong review
python3 scripts/quality_tools.py conflicts

# optional: clone upstream repos for reference under third_party/
bash scripts/fetch_quality_repos.sh
```

## API

- `POST /quality/route` — `{ "comments": "...", "family": "money"|null }`
- `POST /quality/enrich-leads` — `{ "leads": [...], "only_ambiguous": true }`
- `POST /quality/review/enqueue-correct` — sample Correct rows for human review
- `GET  /quality/review/pending`
- `POST /quality/review/verdict` — `{ "id", "human_status", "note" }`
- `POST /quality/conflicts/report`

## n8n (wired in V2)

Live V2 has **Quality Layer Enrich** between Memory Match and Rule Hit Tracker
(`n8n-import/snippets/quality-layer-inline-enrich.js`).

- Reads `$env.QUALITY_LAYER_URL`
- POSTs only ambiguous leads to `/quality/enrich-leads`
- Merges Suggested Status back; no-ops when URL unset or service down

Legacy two-node snippets (`quality-layer-select-ambiguous.js` + merge) remain as reference.

## Argilla (optional)

Set in `.env`:

```bash
ARGILLA_API_URL=...
ARGILLA_API_KEY=...
ARGILLA_WORKSPACE=crm-ai
ARGILLA_DATASET=correct-bucket-review
```

Without a server, exports land in `data/review_queue/argilla_export_*.json` for manual UI import.

## Correct-bucket HITL (routine)

After every large Excel / Telegram validation run:

```bash
python3 scripts/quality_tools.py hitl-routine --input path/to/leads.json --limit 30
python3 scripts/quality_tools.py pending
python3 scripts/quality_tools.py conflicts
```

Goal: catch **Correct but actually Wrong** leaks. Promote confirmed flips into `vault/rules`, `evals/golden_leads.jsonl`, and Memory Match.

