"""The Extractor interface and a spaCy-based base class.

Every extractor returns typed spans. ``label`` is the coarse type used by downstream
scorers and ablations:
    skill        -- a skill/competence (ESCO "skill/competence", SkillSpan skill layer)
    knowledge    -- a body of knowledge / tool / technology (ESCO "knowledge",
                    SkillSpan knowledge layer; noun-chunk spans are labelled this way
                    by heuristic since they are nominal)
    verb_phrase  -- a verb + object/prepositional head, as in the backend matcher
``source`` records which mechanism produced the span (esco | noun_chunk | ner | verb |
model) so ablations can select e.g. "skills-only" vs "+noun chunks" vs "+verb phrases".

Spans carry token offsets (``start``/``end``, end exclusive) into the spaCy Doc, which
for pre-tokenised input (``extract_tokens``) are exactly the input token indices. That
is what span-level evaluation against SkillSpan uses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable, Protocol, Sequence, runtime_checkable

LABELS = ("skill", "knowledge", "verb_phrase")


@dataclass(frozen=True, order=True)
class TypedSpan:
    start: int
    end: int
    text: str
    label: str
    source: str
    start_char: int = -1
    end_char: int = -1
    concept_id: str | None = field(default=None, compare=False)

    def __post_init__(self):
        if self.label not in LABELS:
            raise ValueError(f"Unknown span label {self.label!r}; expected one of {LABELS}")
        if not 0 <= self.start < self.end:
            raise ValueError(f"Bad span offsets ({self.start}, {self.end})")


@runtime_checkable
class Extractor(Protocol):
    name: str

    def extract(self, text: str) -> list[TypedSpan]: ...

    def extract_tokens(self, tokens: Sequence[str]) -> list[TypedSpan]: ...


@lru_cache(maxsize=8)
def load_spacy(model: str, exclude: tuple[str, ...] = ()):
    import spacy

    return spacy.load(model, exclude=list(exclude))


def doc_from_tokens(nlp, tokens: Sequence[str]):
    """A Doc whose tokens are exactly ``tokens`` (whitespace-joined), unprocessed."""
    from spacy.tokens import Doc

    words = [t if t else " " for t in tokens]
    return Doc(nlp.vocab, words=words, spaces=[True] * len(words))


def dedupe_spans(spans: Iterable[TypedSpan]) -> list[TypedSpan]:
    """Keep the first span per (start, end) boundary, then sort by position.

    Earlier spans win, so callers add higher-priority sources first.
    """
    seen: dict[tuple[int, int], TypedSpan] = {}
    for s in spans:
        seen.setdefault((s.start, s.end), s)
    return sorted(seen.values(), key=lambda s: (s.start, s.end, s.label))


def make_span(doc_span, label: str, source: str, text: str | None = None,
              concept_id: str | None = None) -> TypedSpan:
    return TypedSpan(
        start=doc_span.start,
        end=doc_span.end,
        text=text if text is not None else doc_span.text.strip(),
        label=label,
        source=source,
        start_char=doc_span.start_char,
        end_char=doc_span.end_char,
        concept_id=concept_id,
    )


class SpacyExtractor:
    """Base: subclasses set ``self.nlp`` and implement ``spans_from_doc``."""

    name = "spacy"
    nlp = None

    def spans_from_doc(self, doc) -> list[TypedSpan]:
        raise NotImplementedError

    def extract(self, text: str) -> list[TypedSpan]:
        return dedupe_spans(self.spans_from_doc(self.nlp(text)))

    def extract_tokens(self, tokens: Sequence[str]) -> list[TypedSpan]:
        return self.extract_tokens_batch([tokens])[0]

    def extract_batch(self, texts: Sequence[str], batch_size: int = 256) -> list[list[TypedSpan]]:
        return [dedupe_spans(self.spans_from_doc(d)) for d in self.nlp.pipe(texts, batch_size=batch_size)]

    def extract_tokens_batch(self, token_lists: Sequence[Sequence[str]],
                             batch_size: int = 256) -> list[list[TypedSpan]]:
        docs = (doc_from_tokens(self.nlp, toks) for toks in token_lists)
        return [dedupe_spans(self.spans_from_doc(d)) for d in self.nlp.pipe(docs, batch_size=batch_size)]

    def texts(self, text: str) -> list[str]:
        """Unique span strings in first-occurrence order (what scorers embed)."""
        return list(dict.fromkeys(s.text for s in self.extract(text)))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
