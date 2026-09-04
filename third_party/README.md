# Third-party quality tooling

Runtime does **not** import these trees. They are reference clones for the
patterns implemented in `services/quality-layer`.

Fetch with:

```bash
bash scripts/fetch_quality_repos.sh
```

| Repo | Local adapter / use |
|---|---|
| aurelio-labs/semantic-router | RapidFuzz example-bank router (`router.py`) |
| argilla-io/argilla | Correct-bucket review export (`review_queue.py`) |
| snorkel-team/snorkel | Conflict / agree matrix (`conflicts.py`) |
| 567-labs/instructor | Structured LLM outputs (smart-layer) |
| vi3k6i5/flashtext | Phrase strip fallback (`noise_strip.py`) |
| rapidfuzz/RapidFuzz | Fuzzy route scoring (runtime dep) |
| huggingface/setfit | Optional few-shot router (`setfit_router.py`) |
| explosion/spaCy | Optional PhraseMatcher noise strip |
| unionai-oss/pandera | Schema gate (`schema_gate.py`) |
| ksploitx/support-ticket-classifier | Rules→fuzzy→ML→LLM cascade (`cascade.py`) |
| great-expectations/great_expectations | Run checkpoint (`run_checkpoint.py`) |
| erinozolins/eval-loop | HITL / golden promotion loop (`quality_tools.py`) |
| yablokolabs/CallLens | Call-comment quality inspiration (docs) |
| attentiontech/gtm-superintelligence | Pipeline / enrichment inspiration (docs) |
| aiagentwithdhruv/dealpulse | Deal-status distribution inspiration (docs) |

`.gitignore` excludes `third_party/*` clone contents except this README.
