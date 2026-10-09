"""UnionExtractor: spans from several extractors, merged.

Spans with identical token boundaries are deduplicated (the first member wins), so list
the preferred extractor first. Overlapping spans with different boundaries are all
kept; downstream scorers dedupe by string. Offsets are comparable across members only
if they tokenise the same way, which is true for raw-text extraction here because all
members use spaCy's English tokenizer.
"""

from __future__ import annotations

from .base import dedupe_spans


class UnionExtractor:
    def __init__(self, members, name: str = "union"):
        if not members:
            raise ValueError("UnionExtractor needs at least one member")
        self.members = list(members)
        self.name = name

    def extract_batch(self, texts):
        per_member = [m.extract_batch(list(texts)) for m in self.members]
        return [dedupe_spans([s for spans in parts for s in spans]) for parts in zip(*per_member)]

    def extract(self, text):
        return self.extract_batch([text])[0]
