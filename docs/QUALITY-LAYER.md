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

## n8n (optional small branch — not required for Memory Match)

1. After **Memory Match**, add Code node with `n8n-import/snippets/quality-layer-select-ambiguous.js`
2. HTTP Request → `POST {{$env.QUALITY_LAYER_URL}}/quality/enrich-leads`
3. Code node with `n8n-import/snippets/quality-layer-merge-enriched.js`
4. Continue to existing report path

If `QUALITY_LAYER_URL` is unset, skip the branch; live Telegram path stays as today.

## Argilla (optional)

Set in `.env`:

```bash
ARGILLA_API_URL=...
ARGILLA_API_KEY=...
ARGILLA_WORKSPACE=crm-ai
ARGILLA_DATASET=correct-bucket-review
```

Without a server, exports land in `data/review_queue/argilla_export_*.json` for manual UI import.
