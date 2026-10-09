"""Extractors (b) ESCO EntityRuler and (c) ESCO + filtered noun chunks.

Patterns come from the ESCO skills taxonomy CSV (``skills_en.csv`` from the official
download): every preferred label plus every alternative label (newline-separated in the
``altLabels`` column). Matching is case-insensitive and lemma-based:

  * ruler ``esco_lemma`` matches on NORM, which a small component sets to the
    lower-cased lemma of each token, on both the patterns and the text. So
    "managing budgets" matches the label "manage budget".
  * ruler ``esco_lower`` (optional) then matches on LOWER and only adds spans that don't
    overlap existing ones. This catches labels whose out-of-context lemmatisation
    differs from the in-context one.

Each ruler keeps the longest match among overlapping candidates (EntityRuler semantics).
Span ``label`` is ``knowledge`` for ESCO skillType "knowledge" and ``skill`` otherwise,
and ``concept_id`` is the ESCO concept URI.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from spacy.language import Language

from .base import SpacyExtractor, TypedSpan, make_span
from .filters import NounChunkFilter

LEMMA_NORM = "research_lemma_norm"


@Language.component(LEMMA_NORM)
def _lemma_norm(doc):
    for tok in doc:
        tok.norm_ = (tok.lemma_ or tok.text).lower()
    return doc


@dataclass(frozen=True)
class EscoConcept:
    uri: str
    label: str           # "skill" | "knowledge"
    preferred: str
    surface_forms: tuple[str, ...]


def _skill_label(skill_type: str) -> str:
    return "knowledge" if "knowledge" in (skill_type or "").lower() else "skill"


def load_esco_skills(
    csv_path: str | Path,
    include_alt_labels: bool = True,
    include_hidden_labels: bool = False,
    released_only: bool = True,
) -> list[EscoConcept]:
    """Parse ESCO ``skills_en.csv``. Fails loudly if the expected columns are missing."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"ESCO skills CSV not found at {path}. See research/data/README.md for the "
            "manual download instructions."
        )
    concepts: list[EscoConcept] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        if "preferredLabel" not in cols:
            raise ValueError(f"{path} has no 'preferredLabel' column; columns: {sorted(cols)}")
        for row in reader:
            if released_only and "status" in cols and row["status"].strip().lower() not in ("released", ""):
                continue
            forms = [row["preferredLabel"]]
            if include_alt_labels and row.get("altLabels"):
                forms += row["altLabels"].split("\n")
            if include_hidden_labels and row.get("hiddenLabels"):
                forms += row["hiddenLabels"].split("\n")
            forms = [s.strip() for s in forms if s and s.strip()]
            if not forms:
                continue
            concepts.append(
                EscoConcept(
                    uri=row.get("conceptUri", "") or "",
                    label=_skill_label(row.get("skillType", "")),
                    preferred=forms[0],
                    surface_forms=tuple(dict.fromkeys(forms)),
                )
            )
    return concepts


def build_patterns(
    concepts: Iterable[EscoConcept],
    min_label_chars: int = 2,
    max_label_tokens: int = 8,
    drop_stopword_only: bool = True,
    exclude_labels: Iterable[str] = (),
) -> list[dict]:
    """EntityRuler phrase patterns, one per unique (case-folded) surface form.

    When the same surface form belongs to several concepts, the first one in file
    order wins; the collision count is in ``pattern_stats``.
    """
    from spacy.lang.en.stop_words import STOP_WORDS

    excluded = {e.lower() for e in exclude_labels}
    seen: set[str] = set()
    patterns: list[dict] = []
    for c in concepts:
        for form in c.surface_forms:
            key = form.lower()
            if key in seen or key in excluded:
                continue
            toks = key.split()
            if len(form) < min_label_chars or len(toks) > max_label_tokens:
                continue
            if drop_stopword_only and all(t in STOP_WORDS for t in toks):
                continue
            seen.add(key)
            patterns.append({"label": c.label, "pattern": form, "id": c.uri})
    return patterns


class EscoExtractor(SpacyExtractor):
    def __init__(
        self,
        esco_csv: str | Path,
        spacy_model: str = "en_core_web_sm",
        match_attrs: tuple[str, ...] = ("lemma", "lower"),
        include_alt_labels: bool = True,
        include_hidden_labels: bool = False,
        min_label_chars: int = 2,
        max_label_tokens: int = 8,
        drop_stopword_only: bool = True,
        exclude_labels: tuple[str, ...] = (),
        noun_chunks: bool = False,
        noun_chunk_filter: NounChunkFilter | None = None,
        name: str | None = None,
    ):
        self.noun_chunks = noun_chunks
        self.chunk_filter = noun_chunk_filter or NounChunkFilter()
        self.name = name or ("esco+nc" if noun_chunks else "esco")
        exclude = ("ner",) if noun_chunks else ("ner", "parser")
        # A fresh pipeline (not the shared cached one) because we add components to it.
        import spacy

        self.nlp = spacy.load(spacy_model, exclude=list(exclude))
        self.nlp.add_pipe(LEMMA_NORM, after="lemmatizer")

        concepts = load_esco_skills(esco_csv, include_alt_labels, include_hidden_labels)
        patterns = build_patterns(
            concepts, min_label_chars, max_label_tokens, drop_stopword_only, exclude_labels
        )
        self.pattern_stats = {
            "concepts": len(concepts),
            "patterns": len(patterns),
            "csv_sha256": hashlib.sha256(Path(esco_csv).read_bytes()).hexdigest(),
        }
        prev = LEMMA_NORM
        for attr in match_attrs:
            if attr not in ("lemma", "lower"):
                raise ValueError(f"match_attrs entries must be 'lemma' or 'lower', got {attr!r}")
            ruler_name = f"esco_{attr}"
            ruler = self.nlp.add_pipe(
                "entity_ruler",
                name=ruler_name,
                after=prev,
                config={
                    "phrase_matcher_attr": "NORM" if attr == "lemma" else "LOWER",
                    "overwrite_ents": False,
                    "validate": False,
                },
            )
            # Patterns only need the components the match attribute depends on:
            # NORM needs tagger+lemmatizer (not the parser); LOWER needs nothing.
            if attr == "lemma":
                skip = [p for p in ("parser",) if p in self.nlp.pipe_names]
            else:
                skip = [p for p in self.nlp.pipe_names if p != ruler_name]
            with self.nlp.select_pipes(disable=skip):
                ruler.add_patterns(patterns)
            prev = ruler_name

    def spans_from_doc(self, doc) -> list[TypedSpan]:
        spans = [make_span(e, e.label_, "esco", concept_id=e.ent_id_ or None) for e in doc.ents]
        if self.noun_chunks:
            taken = [(s.start, s.end) for s in spans]
            for chunk in doc.noun_chunks:
                sub = self.chunk_filter.apply(chunk)
                if sub is None:
                    continue
                if any(sub.start < e and s < sub.end for s, e in taken):
                    continue  # ESCO match wins over an overlapping noun chunk
                spans.append(make_span(sub, "knowledge", "noun_chunk"))
        return spans
