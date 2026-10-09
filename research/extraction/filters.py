"""Noun-chunk filtering used by extractor (c) (ESCO + filtered noun chunks).

The raw noun chunks from spaCy include pronouns ("She"), determiners ("a nurse") and
generic nouns ("the team", "experience"). The filter:
  1. trims leading/trailing tokens whose POS is in ``trim_pos`` (default DET, PRON,
     PUNCT, CCONJ, ADP) or which are stop words;
  2. drops the chunk if nothing nominal remains (no NOUN/PROPN),
  3. or if its root lemma is in the ``generic_nouns`` stoplist,
  4. or if the span text contains a match of ``drop_regex`` (e.g. anonymisation placeholders
     like "<ORGANIZATION>"),
  5. or if the remaining text is shorter than ``min_chars``.

All of these are config values (configs/extraction.yaml). The stoplist was written
before looking at any SkillSpan evaluation numbers; any later changes must be tuned on
the dev split only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class NounChunkFilter:
    trim_pos: tuple[str, ...] = ("DET", "PRON", "PUNCT", "CCONJ", "ADP", "PART", "NUM")
    trim_stopwords: bool = True
    generic_nouns: frozenset[str] = field(default_factory=frozenset)
    drop_regex: str | None = r"<[A-Z_]+>"
    min_chars: int = 2

    def __post_init__(self):
        self.generic_nouns = frozenset(w.lower() for w in self.generic_nouns)
        self._drop_re = re.compile(self.drop_regex) if self.drop_regex else None

    def _trimmable(self, tok) -> bool:
        return tok.pos_ in self.trim_pos or (self.trim_stopwords and tok.is_stop)

    def apply(self, chunk):
        """Return the filtered sub-span of a spaCy Span, or None if it should be dropped."""
        start, end = chunk.start, chunk.end
        doc = chunk.doc
        while start < end and self._trimmable(doc[start]):
            start += 1
        while end > start and self._trimmable(doc[end - 1]):
            end -= 1
        if start >= end:
            return None
        span = doc[start:end]
        if self._drop_re is not None and self._drop_re.search(span.text):
            return None
        if not any(t.pos_ in ("NOUN", "PROPN") for t in span):
            return None
        if span.root.lemma_.lower() in self.generic_nouns:
            return None
        if len(span.text.strip()) < self.min_chars:
            return None
        return span
