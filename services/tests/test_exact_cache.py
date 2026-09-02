"""Tests for exact fingerprint cache."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rule-engine"))

from exact_cache import ExactClassifyCache, fingerprint  # noqa: E402


def test_exact_cache_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        cache = ExactClassifyCache(path=str(Path(td) / "c.sqlite"))
        lead = {"customer status": "Call Again", "last 10 comments": "na;\nrej;"}
        assert cache.get(lead) is None
        cache.set(lead, {"Suggested Status": "Call Again", "skipAI": True})
        hit = cache.get(lead)
        assert hit and hit["Suggested Status"] == "Call Again" and hit.get("cache_hit") is True
        # different comments = miss
        assert cache.get({**lead, "last 10 comments": "cb tmrw"}) is None
        assert fingerprint(lead) == fingerprint({"customer status": "Call Again", "last 10 comments": "na; rej;"})


if __name__ == "__main__":
    test_exact_cache_roundtrip()
    print("exact-cache-ok")
