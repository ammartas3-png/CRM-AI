"""Exact fingerprint cache for classify results (safe alternative to semantic cache)."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional


def fingerprint(lead: dict[str, Any]) -> str:
    crm = str(lead.get("customer status") or lead.get("Customer Status") or "").strip().lower()
    comments = str(lead.get("last 10 comments") or lead.get("comments") or "")
    # Normalize whitespace only — exact cache, not semantic
    comments = " ".join(comments.split()).lower()
    raw = f"{crm}||{comments}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ExactClassifyCache:
    def __init__(self, path: Optional[str] = None):
        default = Path(os.getenv("CLASSIFY_CACHE_PATH", "/tmp/crm_classify_cache.sqlite"))
        self.path = Path(path) if path else default
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init()

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS classify_cache (
                  fp TEXT PRIMARY KEY,
                  payload TEXT NOT NULL,
                  created_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path), timeout=30)

    def get(self, lead: dict[str, Any], ttl_sec: int = 7 * 24 * 3600) -> Optional[dict[str, Any]]:
        fp = fingerprint(lead)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM classify_cache WHERE fp = ?", (fp,)
            ).fetchone()
            if not row:
                return None
            payload, created = row
            if ttl_sec and (time.time() - float(created)) > ttl_sec:
                conn.execute("DELETE FROM classify_cache WHERE fp = ?", (fp,))
                conn.commit()
                return None
            data = json.loads(payload)
            data["cache_hit"] = True
            data["cache_fingerprint"] = fp
            return data

    def set(self, lead: dict[str, Any], result: dict[str, Any]) -> None:
        fp = fingerprint(lead)
        payload = dict(result)
        payload.pop("cache_hit", None)
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO classify_cache (fp, payload, created_at) VALUES (?, ?, ?)",
                (fp, json.dumps(payload, ensure_ascii=False), time.time()),
            )
            conn.commit()
