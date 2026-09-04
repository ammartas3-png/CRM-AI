# Quality Layer

Adds measurement + ambiguous-lead routing **without rewriting** Memory Match.

## What was added

| Piece | Role | Upstream inspiration |
|---|---|---|
| `services/quality-layer` | FastAPI on `:8050` | — |
| RapidFuzz example-bank router | soft money / agent cb / refusal / language | [semantic-router](https://github.com/aurelio-labs/semantic-router), [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) |
| Noise strip | agent-dial + bare-status phrase removal | [spaCy PhraseMatcher](https://github.com/explosion/spaCy), [FlashText](https://github.com/vi3k6i5/flashtext) |
| Schema gate | required fields + known statuses | [Pandera](https://github.com/unionai-oss/pandera) |
| SetFit / sklearn router | few-shot status when fuzzy is weak | [SetFit](https://github.com/huggingface/setfit) |
| Cascade | rules → fuzzy → ML → `_needs_llm` | [support-ticket-classifier](https://github.com/ksploitx/support-ticket-classifier) |
| Run checkpoint | batch expectation report | [Great Expectations](https://github.com/great-expectations/great_expectations) |
| Correct-bucket review + Argilla export | catch "Correct but wrong" | [Argilla](https://github.com/argilla-io/argilla), [eval-loop](https://github.com/erinozolins/eval-loop) |
| Conflict matrix | engine↔human disagreements by family | [Snorkel](https://github.com/snorkel-team/snorkel) |
| Domain refs | call / GTM / deal pipelines | CallLens, gtm-superintelligence, DealPulse |

## Run locally

```bash
docker compose up -d --build quality-layer
curl http://127.0.0.1:8050/health

# conflict report from golden + wrong review
python3 scripts/quality_tools.py conflicts

# GE-style checkpoint over a leads JSON export
python3 scripts/quality_tools.py checkpoint --input path/to/leads.json

# optional: clone upstream repos for reference under third_party/
bash scripts/fetch_quality_repos.sh
```

Optional heavy backends (SetFit / spaCy / Pandera):

```bash
pip install -r services/quality-layer/requirements-ml.txt
# then set SETFIT_MODEL_PATH=/path/to/trained-setfit
```

Without those packages the service still runs: FlashText-style strip, builtin schema gate, sklearn TF-IDF from golden/wrong review.

## API

- `POST /quality/route` — `{ "comments": "...", "family": "money"|null }`
- `POST /quality/strip-noise` — agent-dial / bare-status cleanup
- `POST /quality/validate-leads` — Pandera-inspired schema gate
- `POST /quality/predict-ml` — SetFit or sklearn few-shot status
- `POST /quality/cascade` — rules → fuzzy → ML → `needs_llm`
- `POST /quality/checkpoint` — GE-style batch expectations
- `POST /quality/enrich-leads` — `{ "leads": [...], "only_ambiguous": true, "use_cascade": false, "strip_noise": true }`
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

To try cascade from n8n, POST with `"use_cascade": true` (default remains fuzzy-only).

## Argilla (optional)

Set in `.env`:

```bash
ARGILLA_API_URL=...
ARGILLA_API_KEY=...
ARGILLA_WORKSPACE=crm-ai
ARGILLA_DATASET=correct-bucket-review
SETFIT_MODEL_PATH=   # optional trained SetFit model dir
```

Without a server, exports land in `data/review_queue/argilla_export_*.json` for manual UI import.

## Correct-bucket HITL (routine)

After every large Excel / Telegram validation run:

```bash
python3 scripts/quality_tools.py hitl-routine --input path/to/leads.json --limit 30
python3 scripts/quality_tools.py pending
python3 scripts/quality_tools.py conflicts
python3 scripts/quality_tools.py checkpoint --input path/to/leads.json
```

Goal: catch **Correct but actually Wrong** leaks. Promote confirmed flips into `vault/rules`, `evals/golden_leads.jsonl`, and Memory Match.
