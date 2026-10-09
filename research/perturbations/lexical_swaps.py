"""Phrase/word swaps from hand-curated YAML lists.

* AffiliationSwap (configs/affiliations.yaml): gendered organisations -> opposite or
  neutral equivalents ("sorority" <-> "fraternity", "Girl Scouts" <-> "Boy Scouts",
  "Society of Women Engineers" -> a neutral engineering society, ...). Phrase matches are
  case-insensitive on token boundaries; capitalisation of the first letter is kept.
* AgenticCommunalRewrite (configs/agentic_communal.yaml): masculine-coded (agentic) words
  <-> feminine-coded (communal) near-synonyms, from the Gaucher et al. (2011) lists the
  backend uses. Each entry is one surface form -> one surface form with an optional
  part-of-speech / dependency constraint, so "led the team" -> "supported the team" but
  "a leading expert" (adjectival) and "lead author" are left alone. Hand-curated: no
  automatic synonyms. Directions are listed separately because some swaps only work one
  way grammatically (e.g. "drove growth" -> "helped growth" but not the reverse).
Both swaps apply all matching entries in one pass (bidirectional where the YAML lists
both directions), and every substitution is logged.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import Replacement, match_case


@dataclass(frozen=True)
class PhraseRule:
    source: tuple[str, ...]      # token sequence (lower-cased unless case_sensitive)
    target: str
    note: str
    case_sensitive: bool = False


class AffiliationSwap:
    name = "affiliation_swap"

    def __init__(self, pairs: list[dict], tokenizer):
        """``pairs``: [{a, b, bidirectional?, case_sensitive?}] -- a -> b (and b -> a)."""
        rules = []
        for p in pairs:
            cs = bool(p.get("case_sensitive", False))
            norm = (lambda x: x) if cs else str.lower
            rules.append(PhraseRule(tuple(norm(t.text) for t in tokenizer(p["a"])), p["b"], f"{p['a']} -> {p['b']}", cs))
            if p.get("bidirectional", True):
                rules.append(PhraseRule(tuple(norm(t.text) for t in tokenizer(p["b"])), p["a"], f"{p['b']} -> {p['a']}", cs))
        # longest first so "Society of Women Engineers" wins over "women"
        self.rules = sorted(rules, key=lambda r: -len(r.source))

    def replacements(self, doc, gender: str = "", key: str = "") -> list[Replacement]:
        raw = [t.text for t in doc]
        low = [w.lower() for w in raw]
        out, taken = [], set()
        for r in self.rules:
            n = len(r.source)
            seq = raw if r.case_sensitive else low
            for i in range(len(seq) - n + 1):
                if tuple(seq[i : i + n]) == r.source and not taken & set(range(i, i + n)):
                    out.append(Replacement(i, i + n, match_case(doc[i].text, r.target), "affiliation", r.note))
                    taken |= set(range(i, i + n))
        return out


@dataclass(frozen=True)
class WordRule:
    source: str
    target: str
    direction: str            # "agentic->communal" | "communal->agentic"
    pos: frozenset | None     # allowed coarse POS tags
    not_dep: frozenset | None # forbidden dependency labels (e.g. amod for "a leading expert")
    dep: frozenset | None = None   # if set, the token's dependency label must be one of these
    no_passive: bool = False       # skip passive uses ("is supported by NIH")
    idiom_guard: bool = False      # skip "led to" (= caused), phrasal verbs ("drive out"), "lead the way"


# Objects that make lead/support idiomatic or template text (found in dev samples, 2026-10-09):
# "lead the way", "lead a ... life", physician-directory boilerplate "practice supports these languages".
_FIXED_OBJECTS = {"way", "life", "language"}


def _idiomatic(tok) -> bool:
    """Uses where a lead/drive/support swap changes meaning or breaks grammar."""
    nxt_tok = tok.doc[tok.i + 1] if tok.i + 1 < len(tok.doc) else None
    nxt = nxt_tok.text.lower() if nxt_tok is not None else ""
    kids = list(tok.children)
    if tok.tag_ == "VBG" and nxt_tok is not None and nxt_tok.pos_ in ("NOUN", "PROPN", "ADJ"):
        return True                                     # attributive "the world's leading researchers"
    if nxt == "to" or any(c.dep_ == "prep" and c.text.lower() == "to" for c in kids):
        return True                                     # "led to her interest" (= caused)
    if any(c.dep_ == "prt" for c in kids):
        return True                                     # "driving out the poor"
    if any(c.dep_ in ("dobj", "obj") and c.lemma_.lower() in _FIXED_OBJECTS for c in kids):
        return True                                     # "leading the way", "lead a life", "supports this language"
    has_obj = any(c.dep_ in ("dobj", "obj") for c in kids)
    if has_obj and any(c.dep_ in ("xcomp", "ccomp") for c in kids):
        return True                                     # "lead her to embark", "support X to do Y"
    return False


class AgenticCommunalRewrite:
    name = "agentic_communal"

    def __init__(self, entries: list[dict]):
        self.rules: dict[str, WordRule] = {}
        for e in entries:
            src = e["from"].lower()
            if src in self.rules:
                raise ValueError(f"agentic_communal.yaml: duplicate source word {src!r}")
            self.rules[src] = WordRule(src, e["to"], e["direction"],
                                       frozenset(e["pos"]) if e.get("pos") else None,
                                       frozenset(e["not_dep"]) if e.get("not_dep") else None,
                                       frozenset(e["dep"]) if e.get("dep") else None,
                                       bool(e.get("no_passive", False)),
                                       bool(e.get("idiom_guard", False)))

    def replacements(self, doc, gender: str = "", key: str = "") -> list[Replacement]:
        out = []
        for tok in doc:
            r = self.rules.get(tok.text.lower())
            if r is None:
                continue
            prev = doc[tok.i - 1].text if tok.i > 0 else ""
            nxt = doc[tok.i + 1].text if tok.i + 1 < len(doc) else ""
            if prev == "-" or nxt == "-":
                continue                                # hyphenated compound: "tech-driven"
            if r.pos is not None and tok.pos_ not in r.pos:
                continue
            if r.not_dep is not None and tok.dep_ in r.not_dep:
                continue
            if r.dep is not None and tok.dep_ not in r.dep:
                continue
            if r.no_passive and (any(c.dep_ in ("auxpass", "agent") for c in tok.children) or tok.dep_ == "acl"):
                continue
            if r.idiom_guard and _idiomatic(tok):
                continue
            out.append(Replacement(tok.i, tok.i + 1, match_case(tok.text, r.target), r.direction,
                                   f"{tok.text}->{r.target} ({tok.pos_}/{tok.dep_})"))
        return out
