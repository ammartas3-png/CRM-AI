"""Semantic example bank — RapidFuzz now, sentence-transformers optional later.

Inspired by aurelio-labs/semantic-router + huggingface/sentence-transformers.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from rapidfuzz import fuzz

from routes_bank import ROUTE_BANK

_example_vecs = None


def _fold(s: str) -> str:
    return " ".join(str(s or "").lower().split())


@lru_cache(maxsize=1)
def _try_load_embedder():
    path = os.getenv("SEMANTIC_MODEL_PATH", "").strip()
    if not path:
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer(path)
    except Exception:
        return None


def _build_example_index(model):
    global _example_vecs
    if _example_vecs is not None:
        return _example_vecs
    texts: list[str] = []
    meta: list[tuple[str, str, str]] = []
    for rid, spec in ROUTE_BANK.items():
        status = str(spec.get("status") or "")
        family = str(spec.get("family") or "")
        for ex in spec.get("examples") or []:
            texts.append(str(ex))
            meta.append((rid, status, family))
    vecs = model.encode(texts, normalize_embeddings=True)
    _example_vecs = [(meta[i][0], meta[i][1], meta[i][2], vecs[i]) for i in range(len(texts))]
    return _example_vecs


def semantic_route(comments: str, *, min_score: float = 72.0, family: str | None = None) -> dict[str, Any]:
    text = _fold(comments)
    if not text:
        return {
            "matched": False,
            "status": None,
            "score": 0.0,
            "route_id": None,
            "family": family,
            "backend": "empty",
            "inspired_by": "semantic-router + sentence-transformers",
        }

    model = _try_load_embedder()
    embed_err = None
    if model is not None:
        try:
            import numpy as np

            q = model.encode([comments], normalize_embeddings=True)[0]
            best = None
            best_score = -1.0
            for rid, status, fam, vec in _build_example_index(model):
                if family and fam != family:
                    continue
                score = float(np.dot(q, vec) * 100.0)
                if score > best_score:
                    best_score = score
                    best = (rid, status, fam, score)
            if best and best_score >= min_score:
                return {
                    "matched": True,
                    "status": best[1],
                    "score": round(best_score, 2),
                    "route_id": best[0],
                    "family": best[2],
                    "backend": "sentence-transformers",
                    "inspired_by": "semantic-router + sentence-transformers",
                }
            return {
                "matched": False,
                "status": None,
                "score": round(best_score, 2) if best else 0.0,
                "route_id": best[0] if best else None,
                "family": family,
                "backend": "sentence-transformers",
                "inspired_by": "semantic-router + sentence-transformers",
            }
        except Exception as exc:
            embed_err = str(exc)

    best = None
    best_score = -1.0
    for rid, spec in ROUTE_BANK.items():
        fam = str(spec.get("family") or "")
        if family and fam != family:
            continue
        status = str(spec.get("status") or "")
        for ex in spec.get("examples") or []:
            score = float(
                max(
                    fuzz.token_set_ratio(text, _fold(ex)),
                    fuzz.partial_ratio(text, _fold(ex)),
                )
            )
            if score > best_score:
                best_score = score
                best = (rid, status, fam, score)

    matched = bool(best and best_score >= min_score)
    return {
        "matched": matched,
        "status": best[1] if matched and best else None,
        "score": round(best_score, 2) if best else 0.0,
        "route_id": best[0] if best else None,
        "family": best[2] if best else family,
        "backend": "rapidfuzz",
        "embedder_error": embed_err,
        "inspired_by": "semantic-router + sentence-transformers",
    }
