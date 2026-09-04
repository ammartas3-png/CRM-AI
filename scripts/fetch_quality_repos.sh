#!/usr/bin/env bash
# Clone optional upstream quality repos as reference (not runtime-required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="$ROOT/third_party"
mkdir -p "$VENDOR"

clone_ref() {
  local url="$1"
  local name="$2"
  if [[ -d "$VENDOR/$name/.git" ]]; then
    echo "exists: $name"
    return 0
  fi
  echo "cloning $name ..."
  git clone --depth 1 "$url" "$VENDOR/$name"
}

# Core quality stack
clone_ref https://github.com/aurelio-labs/semantic-router.git semantic-router
clone_ref https://github.com/argilla-io/argilla.git argilla
clone_ref https://github.com/snorkel-team/snorkel.git snorkel
clone_ref https://github.com/567-labs/instructor.git instructor
clone_ref https://github.com/vi3k6i5/flashtext.git flashtext
clone_ref https://github.com/rapidfuzz/RapidFuzz.git rapidfuzz

# P0 — local adapters in services/quality-layer
clone_ref https://github.com/huggingface/setfit.git setfit
clone_ref https://github.com/explosion/spaCy.git spacy
clone_ref https://github.com/unionai-oss/pandera.git pandera
clone_ref https://github.com/ksploitx/support-ticket-classifier.git support-ticket-classifier

# P1
clone_ref https://github.com/great-expectations/great_expectations.git great_expectations
clone_ref https://github.com/erinozolins/eval-loop.git eval-loop

# P2 domain inspiration
clone_ref https://github.com/yablokolabs/CallLens.git calllens
clone_ref https://github.com/attentiontech/gtm-superintelligence.git gtm-superintelligence
clone_ref https://github.com/aiagentwithdhruv/dealpulse.git dealpulse

echo "Done. Runtime uses services/quality-layer adapters; clones are reference only under third_party/."
