"""Shared machinery for counterfactual perturbations.

A perturbation inspects a parsed spaCy Doc and proposes replacements of token ranges.
``apply_replacements`` rebuilds the text from the tokens, keeping all original whitespace,
so only the replaced words change. Every replacement is logged as a ``Change``.

All perturbers work on the same Doc (each bio is parsed once by ``parse``), and a
composite perturbation simply merges the replacement lists of its parts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Iterable, Protocol, Sequence


@dataclass(frozen=True)
class Replacement:
    start: int            # token index (inclusive)
    end: int              # token index (exclusive)
    new_text: str
    kind: str             # e.g. "pronoun", "name", "affiliation", "agentic->communal"
    note: str = ""


@dataclass(frozen=True)
class Change:
    kind: str
    original: str
    replacement: str
    start_char: int       # in the perturbed text
    end_char: int
    note: str = ""
    orig_start: int = -1  # in the original text
    orig_end: int = -1


@dataclass
class PerturbResult:
    text: str
    changes: list[Change] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.changes)

    def changes_json(self) -> str:
        return json.dumps([asdict(c) for c in self.changes], ensure_ascii=False)


class Perturber(Protocol):
    name: str

    def replacements(self, doc, gender: str, key: str) -> list[Replacement]: ...


def match_case(source: str, target: str) -> str:
    """Give ``target`` the capitalisation pattern of ``source`` (UPPER, Title, lower)."""
    if not source:
        return target
    if source.isupper() and len(source) > 1:
        return target.upper()
    if source[0].isupper():
        return target[:1].upper() + target[1:]
    return target[:1].lower() + target[1:] if target[:1].isupper() and not target.isupper() else target


def merge(replacement_lists: Iterable[Sequence[Replacement]]) -> list[Replacement]:
    """Combine replacements from several perturbers; overlapping later ones are dropped."""
    taken: list[tuple[int, int]] = []
    out: list[Replacement] = []
    for reps in replacement_lists:
        for r in sorted(reps, key=lambda x: (x.start, x.end)):
            if any(r.start < e and s < r.end for s, e in taken):
                continue
            taken.append((r.start, r.end))
            out.append(r)
    return sorted(out, key=lambda x: x.start)


def apply_replacements(doc, reps: Sequence[Replacement]) -> PerturbResult:
    reps = merge([reps])
    parts: list[str] = []
    changes: list[Change] = []
    i = 0
    for r in reps:
        for tok in doc[i : r.start]:
            parts.append(tok.text_with_ws)
        span = doc[r.start : r.end]
        trailing = doc[r.end - 1].whitespace_
        new_start = sum(len(p) for p in parts)   # char offset of the replacement in the new text
        parts.append(r.new_text + trailing)
        if r.new_text != span.text:
            changes.append(Change(r.kind, span.text, r.new_text, new_start, new_start + len(r.new_text), r.note,
                                  span.start_char, span.end_char))
        i = r.end
    for tok in doc[i:]:
        parts.append(tok.text_with_ws)
    return PerturbResult("".join(parts), changes)


def parse(nlp, texts: Sequence[str], batch_size: int = 256):
    return nlp.pipe(texts, batch_size=batch_size)
