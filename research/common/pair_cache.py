"""Disk caches for things computed per text or per (resume, JD) pair.

* PairScoreCache: float scores for pairwise models (cross-encoder, LLM judge), keyed by
  (namespace, sha256(jd), sha256(resume)). Pair order matters and is fixed: (resume, jd).
* JsonCache: arbitrary JSON values per text (e.g. extracted entity spans), keyed by
  (namespace, sha256(text)).
One SQLite file per namespace, as with the embedding cache.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Sequence

from .config import RESEARCH_ROOT
from .embedding_cache import _safe_filename, text_key

DEFAULT_DIR = RESEARCH_ROOT / ".cache"


class _Store:
    def __init__(self, namespace: str, cache_dir: Path, value_type: str):
        self.namespace = namespace
        self.path = Path(cache_dir) / _safe_filename(namespace)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(f"CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value {value_type})")
        self._conn.commit()

    def _get(self, keys: Sequence[str]) -> dict[str, Any]:
        out = {}
        unique = list(dict.fromkeys(keys))
        for i in range(0, len(unique), 500):
            chunk = unique[i : i + 500]
            marks = ",".join("?" * len(chunk))
            for k, v in self._conn.execute(f"SELECT key, value FROM kv WHERE key IN ({marks})", chunk):
                out[k] = v
        return out

    def _put(self, items: dict[str, Any]) -> None:
        self._conn.executemany("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", list(items.items()))
        self._conn.commit()

    def __len__(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM kv").fetchone()[0])

    def close(self) -> None:
        self._conn.close()


def pair_key(resume: str, jd: str) -> str:
    return f"{text_key(jd)}:{text_key(resume)}"


class PairScoreCache(_Store):
    def __init__(self, namespace: str, cache_dir: str | Path = DEFAULT_DIR / "pair_scores"):
        super().__init__(namespace, Path(cache_dir), "REAL")

    def get_many(self, pairs: Sequence[tuple[str, str]]) -> dict[str, float]:
        return self._get([pair_key(r, j) for r, j in pairs])

    def put_many(self, scores: dict[tuple[str, str], float]) -> None:
        self._put({pair_key(r, j): float(s) for (r, j), s in scores.items()})


class JsonCache(_Store):
    def __init__(self, namespace: str, cache_dir: str | Path = DEFAULT_DIR / "json"):
        super().__init__(namespace, Path(cache_dir), "TEXT")

    def get_many(self, texts: Sequence[str]) -> dict[str, Any]:
        raw = self._get([text_key(t) for t in texts])
        return {k: json.loads(v) for k, v in raw.items()}

    def put_many(self, items: dict[str, Any]) -> None:
        self._put({text_key(t): json.dumps(v) for t, v in items.items()})
