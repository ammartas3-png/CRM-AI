"""Optional SetFit / sklearn few-shot status router for ambiguous comments.

- If SETFIT_MODEL_PATH is set and `setfit` is installed → use SetFit.
- Else fit/load a lightweight TF-IDF + LogisticRegression fallback from
  evals/golden_leads.jsonl + evals/wrong_review_cases.jsonl (always available).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_WS = re.compile(r"\s+")
_MODEL = None
_BACKEND = "none"
_LABELS: list[str] = []


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _fold(text: str) -> str:
    t = str(text or "").lower()
    t = t.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ç", "c")
    t = t.replace("ö", "o").replace("ü", "u")
    t = t.replace("\n", " ").replace("|", " ")
    return _WS.sub(" ", t).strip()


def _load_training_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for name in ("golden_leads.jsonl", "wrong_review_cases.jsonl"):
        path = _root() / "evals" / name
        if not path.exists():
            path = Path("/app/evals") / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            text = str(row.get("last 10 comments") or row.get("comments") or "")
            label = str(
                row.get("expect_status")
                or row.get("Suggested Status")
                or row.get("human_status")
                or ""
            ).strip()
            if text and label:
                pairs.append((_fold(text), label))
    return pairs


def _fit_sklearn(pairs: list[tuple[str, str]]) -> Any:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    X = [t for t, _ in pairs]
    y = [lab for _, lab in pairs]
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000)),
            ("clf", LogisticRegression(max_iter=400, class_weight="balanced")),
        ]
    )
    pipe.fit(X, y)
    return pipe


def ensure_model() -> str:
    """Load or train model once. Returns backend name."""
    global _MODEL, _BACKEND, _LABELS
    if _MODEL is not None:
        return _BACKEND

    model_path = os.getenv("SETFIT_MODEL_PATH", "").strip()
    if model_path:
        try:
            from setfit import SetFitModel  # type: ignore

            _MODEL = SetFitModel.from_pretrained(model_path)
            _BACKEND = "setfit"
            return _BACKEND
        except Exception:
            pass

    pairs = _load_training_pairs()
    if len(pairs) < 8:
        _BACKEND = "none"
        return _BACKEND
    try:
        _MODEL = _fit_sklearn(pairs)
        _LABELS = sorted({lab for _, lab in pairs})
        _BACKEND = "sklearn-tfidf"
    except Exception:
        _BACKEND = "none"
    return _BACKEND


def predict_status(comments: str) -> dict[str, Any]:
    backend = ensure_model()
    text = _fold(comments)
    if not text or _MODEL is None or backend == "none":
        return {
            "matched": False,
            "status": None,
            "score": 0.0,
            "backend": backend,
            "reason": "model unavailable or empty text",
        }

    if backend == "setfit":
        try:
            pred = _MODEL.predict([text])[0]
            # SetFit may not expose probs easily on all heads
            return {
                "matched": True,
                "status": str(pred),
                "score": 80.0,
                "backend": backend,
                "reason": "setfit predict",
            }
        except Exception as exc:
            return {
                "matched": False,
                "status": None,
                "score": 0.0,
                "backend": backend,
                "reason": f"setfit error: {exc}",
            }

    # sklearn
    try:
        proba = _MODEL.predict_proba([text])[0]
        classes = list(_MODEL.named_steps["clf"].classes_)
        idx = int(proba.argmax())
        score = float(proba[idx]) * 100.0
        return {
            "matched": score >= 35.0,
            "status": str(classes[idx]),
            "score": round(score, 2),
            "backend": backend,
            "reason": "sklearn tfidf+logreg",
            "labels": _LABELS,
        }
    except Exception as exc:
        return {
            "matched": False,
            "status": None,
            "score": 0.0,
            "backend": backend,
            "reason": f"sklearn error: {exc}",
        }
