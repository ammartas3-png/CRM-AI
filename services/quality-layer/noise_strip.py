"""Agent-dial / bare-status noise stripper (spaCy PhraseMatcher + FlashText inspired).

Optional runtime: spaCy PhraseMatcher when `spacy` is installed.
Always-on fallback: FlashText-style keyword replacement (pure Python).
"""

from __future__ import annotations

import re
from typing import Any

# Agent redial / voicemail notes — not customer callbacks.
AGENT_DIAL_PHRASES: list[str] = [
    "cb : vm",
    "cb:vm",
    "cb vm",
    "cb na",
    "cb ndt",
    "cb db",
    "cb rej",
    "cb:na",
    "cb:rej",
    "callback na",
    "callback vm",
    "call again rej",
    "called back puhu",
    "called back pu hu",
    "i said i would hang up and call back",
    "when i tried to cb",
    "after i cb",
    "i tried to cb",
    "i will hang up and call back",
]

# Bare CRM status pastes that are labels, not evidence.
BARE_STATUS_PHRASES: list[str] = [
    "no potential",
    "call again",
    "recall",
    "no interest",
    "no language",
    "no answer",
    "denied registration",
    "wrong number",
]

_WS = re.compile(r"\s+")


def _fold(text: str) -> str:
    t = str(text or "").lower()
    t = t.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ç", "c")
    t = t.replace("ö", "o").replace("ü", "u")
    return _WS.sub(" ", t).strip()


def _flash_replace(text: str, phrases: list[str], replacement: str = " ") -> str:
    """FlashText-inspired longest-phrase replacement without the dependency."""
    t = _fold(text)
    # longest first to avoid partial eats
    for phrase in sorted({_fold(p) for p in phrases}, key=len, reverse=True):
        if not phrase:
            continue
        t = t.replace(phrase, replacement)
    return _WS.sub(" ", t).strip()


def _spacy_strip(text: str, phrases: list[str]) -> str | None:
    try:
        import spacy
        from spacy.matcher import PhraseMatcher
    except Exception:
        return None
    try:
        nlp = spacy.blank("en")
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(p) for p in phrases if p.strip()]
        matcher.add("NOISE", patterns)
        doc = nlp.make_doc(text)
        spans = [doc[s:e] for _, s, e in matcher(doc)]
        if not spans:
            return text
        # remove matched spans
        drop = set()
        for span in spans:
            drop.update(range(span.start, span.end))
        kept = [tok.text for i, tok in enumerate(doc) if i not in drop]
        return _WS.sub(" ", " ".join(kept)).strip()
    except Exception:
        return None


def strip_noise(comments: str, *, use_spacy: bool = True) -> dict[str, Any]:
    """Strip agent-dial + bare-status noise. Returns cleaned text + meta."""
    raw = str(comments or "")
    phrases = AGENT_DIAL_PHRASES + BARE_STATUS_PHRASES
    backend = "flashtext-style"
    cleaned = raw
    if use_spacy:
        spacy_out = _spacy_strip(raw, phrases)
        if spacy_out is not None:
            cleaned = spacy_out
            backend = "spacy-phrase-matcher"
        else:
            cleaned = _flash_replace(raw, phrases)
    else:
        cleaned = _flash_replace(raw, phrases)

    removed = len(_fold(raw)) - len(_fold(cleaned))
    return {
        "original": raw,
        "cleaned": cleaned,
        "backend": backend,
        "chars_removed_approx": max(0, removed),
        "phrases_configured": len(phrases),
    }
