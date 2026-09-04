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

clone_ref https://github.com/aurelio-labs/semantic-router.git semantic-router
clone_ref https://github.com/argilla-io/argilla.git argilla
clone_ref https://github.com/snorkel-team/snorkel.git snorkel
clone_ref https://github.com/567-labs/instructor.git instructor
clone_ref https://github.com/vi3k6i5/flashtext.git flashtext

echo "Done. Runtime still uses services/quality-layer (RapidFuzz local router)."
echo "These clones are reference material under third_party/."
