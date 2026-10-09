"""Extractor (a): a faithful port of the backend's ``extract_entities``.

Mirrors backend/app/services/matcher.py at commit 60bfe79 so the paper's "naive entity
matcher" baseline is exactly what the app does. A parity test checks that ``texts()``
gives the same set of strings as the backend function. Differences:
  * it returns typed spans with offsets instead of a bag of strings;
  * the output order is deterministic (sorted by position), not set order.

Verb "phrases" in the backend are a verb plus the *head words* of some children (e.g.
"led a team" -> "led team"), which is not a contiguous span. For evaluation the span
covers the verb through its furthest included child, and ``text`` keeps the backend
string.
"""

from __future__ import annotations

from .base import SpacyExtractor, TypedSpan, load_spacy, make_span
from .filters import NounChunkFilter


class NounChunkExtractor(SpacyExtractor):
    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        ner_labels: tuple[str, ...] = ("ORG", "PRODUCT", "GPE", "WORK_OF_ART"),
        min_chunk_chars: int = 3,
        max_chunk_chars: int = 59,
        verb_deps: tuple[str, ...] = ("ROOT", "conj", "advcl"),
        verb_child_deps: tuple[str, ...] = ("dobj", "attr", "prep"),
        min_verb_phrase_chars: int = 4,
        use_ner: bool = True,
        use_noun_chunks: bool = True,
        use_verb_phrases: bool = True,
        name: str = "noun_chunk",
    ):
        self.name = name
        self.nlp = load_spacy(spacy_model)
        self.ner_labels = set(ner_labels)
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        self.verb_deps = set(verb_deps)
        self.verb_child_deps = set(verb_child_deps)
        self.min_verb_phrase_chars = min_verb_phrase_chars
        self.use_ner = use_ner
        self.use_noun_chunks = use_noun_chunks
        self.use_verb_phrases = use_verb_phrases

    def spans_from_doc(self, doc) -> list[TypedSpan]:
        spans: list[TypedSpan] = []
        if self.use_ner:
            for ent in doc.ents:
                if ent.label_ in self.ner_labels and ent.text.strip():
                    spans.append(make_span(ent, "knowledge", "ner"))
        if self.use_noun_chunks:
            for chunk in doc.noun_chunks:
                text = chunk.text.strip()
                # backend: 2 < len(text) < 60
                if self.min_chunk_chars <= len(text) <= self.max_chunk_chars:
                    spans.append(make_span(chunk, "knowledge", "noun_chunk"))
        if self.use_verb_phrases:
            for token in doc:
                if token.pos_ != "VERB" or token.dep_ not in self.verb_deps:
                    continue
                kids = [c for c in token.children if c.dep_ in self.verb_child_deps]
                phrase = " ".join([token.text] + [c.text for c in kids]).strip()
                # backend: len(phrase) > 3
                if len(phrase) >= self.min_verb_phrase_chars:
                    idx = [token.i] + [c.i for c in kids]
                    span = doc[min(idx) : max(idx) + 1]
                    spans.append(make_span(span, "verb_phrase", "verb", text=phrase))
        return spans


class FilteredNounChunkExtractor(SpacyExtractor):
    """Noun chunks passed through ``NounChunkFilter`` only (no NER, no verbs, no ESCO).

    Not one of the three required extractors; reported to separate how much of
    extractor (c) comes from the filter vs from ESCO.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm",
                 noun_chunk_filter: NounChunkFilter | None = None, name: str = "filtered_nc"):
        self.name = name
        self.nlp = load_spacy(spacy_model, ("ner",))
        self.chunk_filter = noun_chunk_filter or NounChunkFilter()

    def spans_from_doc(self, doc) -> list[TypedSpan]:
        spans = []
        for chunk in doc.noun_chunks:
            sub = self.chunk_filter.apply(chunk)
            if sub is not None:
                spans.append(make_span(sub, "knowledge", "noun_chunk"))
        return spans
