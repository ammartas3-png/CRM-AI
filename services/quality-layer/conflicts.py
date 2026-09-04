"""Snorkel-style conflict matrix without requiring Snorkel as a hard dependency."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _pick(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for k in keys:
        if row.get(k):
            return str(row[k]).strip()
    return ""


def _family(note: str, engine: str, human: str) -> str:
    blob = f"{note} {engine} {human}".lower()
    if re.search(r"money|afford|funds|salary|capital|no potential", blob):
        return "money"
    if re.search(r"callback|call again|cb:|agent dial|redial|busy_after", blob):
        return "callback"
    if re.search(r"refus|recall|no interest|playing|leave it|scam|cancel", blob):
        return "refusal"
    if re.search(r"language|english|mandarin", blob):
        return "language"
    if re.search(r"no answer|na\b|vm\b", blob):
        return "no_answer"
    return "other"


def build_conflict_report(paths: Iterable[Path]) -> dict[str, Any]:
    pairs: Counter[tuple[str, str]] = Counter()
    by_family: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    total = 0
    agree = 0

    for path in paths:
        for row in _load_jsonl(path):
            eng = _pick(row, ("engine_was", "engine", "prev_status"))
            hum = _pick(row, ("expect_status", "human", "human_status"))
            if not eng or not hum:
                eng = eng or _pick(row, ("Suggested Status", "customer status"))
                hum = hum or _pick(row, ("expect_status", "Suggested Status"))
            if not eng or not hum:
                continue
            total += 1
            if eng.lower() == hum.lower() or (
                "no potential" in eng.lower() and "no potential" in hum.lower()
            ):
                agree += 1
                continue
            key = (eng, hum)
            pairs[key] += 1
            fam = _family(str(row.get("note") or ""), eng, hum)
            by_family[fam][key] += 1
            if len(samples[fam]) < 5:
                samples[fam].append(
                    {
                        "account": _pick(row, ("account no", "account", "account_no")),
                        "engine": eng,
                        "human": hum,
                        "note": str(row.get("note") or "")[:160],
                        "source": path.name,
                    }
                )

    return {
        "total_labeled": total,
        "agree": agree,
        "disagree": total - agree,
        "agree_rate": round(agree / total, 4) if total else 0.0,
        "top_conflicts": [
            {"engine": a, "human": b, "count": c} for (a, b), c in pairs.most_common(20)
        ],
        "by_family": {
            fam: [
                {"engine": a, "human": b, "count": c} for (a, b), c in ctr.most_common(10)
            ]
            for fam, ctr in sorted(by_family.items(), key=lambda x: -sum(x[1].values()))
        },
        "samples": samples,
    }


def write_report(report: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
