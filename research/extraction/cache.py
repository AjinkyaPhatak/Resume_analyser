"""Disk-cached extraction: run an extractor once per distinct text, ever.

The cache namespace is the extractor's ``cache_id`` (name + a fingerprint of its config
spec), so changing extractor settings never returns stale spans.
"""

from __future__ import annotations

import hashlib
import json
from typing import Sequence

from research.common.pair_cache import DEFAULT_DIR, JsonCache

from .base import TypedSpan


def spec_fingerprint(spec: dict, extra: dict | None = None) -> str:
    blob = json.dumps({"spec": spec, "extra": extra or {}}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _to_json(spans: list[TypedSpan]) -> list[dict]:
    return [{"start": s.start, "end": s.end, "text": s.text, "label": s.label, "source": s.source,
             "start_char": s.start_char, "end_char": s.end_char, "concept_id": s.concept_id} for s in spans]


def _from_json(items: list[dict]) -> list[TypedSpan]:
    return [TypedSpan(**d) for d in items]


class CachedExtractor:
    """Wraps any Extractor; ``extract_batch(texts)`` only runs the extractor on misses."""

    def __init__(self, extractor, cache_id: str, cache_dir=DEFAULT_DIR / "extraction"):
        self.extractor = extractor
        self.name = getattr(extractor, "name", "extractor")
        self.cache = JsonCache(f"extract|{cache_id}", cache_dir)
        self.n_extracted = 0

    def extract_batch(self, texts: Sequence[str]) -> list[list[TypedSpan]]:
        texts = list(texts)
        hits = self.cache.get_many(texts)
        from research.common.embedding_cache import text_key

        missing = list(dict.fromkeys(t for t in texts if text_key(t) not in hits))
        if missing:
            if hasattr(self.extractor, "extract_batch"):
                results = self.extractor.extract_batch(missing)
            else:
                results = [self.extractor.extract(t) for t in missing]
            new = {t: _to_json(r) for t, r in zip(missing, results)}
            self.cache.put_many(new)
            hits.update({text_key(t): v for t, v in new.items()})
            self.n_extracted += len(missing)
        return [_from_json(hits[text_key(t)]) for t in texts]

    def extract(self, text: str) -> list[TypedSpan]:
        return self.extract_batch([text])[0]
