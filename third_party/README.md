# Third-party quality tooling

Runtime does **not** import these trees. They are reference clones for the
patterns implemented in `services/quality-layer`.

Fetch with:

```bash
bash scripts/fetch_quality_repos.sh
```

| Repo | Why we care |
|---|---|
| aurelio-labs/semantic-router | Ambiguous family routing by examples |
| argilla-io/argilla | Human review UI for Correct-bucket audits |
| snorkel-team/snorkel | Labeling-function conflict / agree matrix |
| 567-labs/instructor | Structured LLM outputs (already used in smart-layer) |
| vi3k6i5/flashtext | Fast keyword dictionaries (optional later) |

`.gitignore` excludes `third_party/*` clone contents except this README.
