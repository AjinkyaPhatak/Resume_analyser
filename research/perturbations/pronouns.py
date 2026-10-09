"""pronoun_swap: he<->she, him/his<->her, hers<->his, himself<->herself, Mr<->Ms.

The swap is BIDIRECTIONAL over the whole text (as in counterfactual data augmentation,
Lu et al. 2018; Zhao et al. 2018): every gendered pronoun flips, including ones that
refer to other people (e.g. "her husband ... he"), so the counterfactual stays coherent.

Ambiguity heuristic (documented for the paper):
  * "her" -> "his" when spaCy tags it PRP$ (possessive determiner: "her lab"),
           -> "him" otherwise (object: "taught her").
    Fallback when the tag is neither PRP$ nor PRP: "his" if the next token is a NOUN,
    PROPN, ADJ or NUM, else "him".
  * "his" -> "hers" when standalone, decided by the NEXT token (end of text, punctuation,
           verb, auxiliary, conjunction, adposition, pronoun or determiner: "the choice was
           his.", "his and hers"), because spaCy often tags standalone "his" as PRP$;
           otherwise -> "her" ("his lab").
  * "hers" -> "his".
  * Titles: Mr/Mr. -> Ms/Ms.; Ms, Mrs, Miss (with or without '.') -> Mr. The period is a
    separate token or part of the title token depending on the tokenizer; both work.
Capitalisation is preserved (He -> She, HIS -> HER).
"""

from __future__ import annotations

from .base import Replacement, match_case

SIMPLE = {
    "he": "she", "she": "he",
    "him": "her",
    "hers": "his",
    "himself": "herself", "herself": "himself",
    "mr": "ms", "mr.": "ms.",
    "ms": "mr", "ms.": "mr.", "mrs": "mr", "mrs.": "mr.", "miss": "mr",
}


def her_target(tok) -> str:
    if tok.tag_ == "PRP$":
        return "his"
    if tok.tag_ == "PRP":
        return "him"
    nxt = tok.doc[tok.i + 1] if tok.i + 1 < len(tok.doc) else None
    return "his" if nxt is not None and nxt.pos_ in ("NOUN", "PROPN", "ADJ", "NUM") else "him"


def his_target(tok) -> str:
    nxt = tok.doc[tok.i + 1] if tok.i + 1 < len(tok.doc) else None
    if nxt is None or nxt.is_punct or nxt.pos_ in ("VERB", "AUX", "CCONJ", "ADP", "PRON", "DET"):
        return "hers"
    return "her"


class PronounSwap:
    name = "pronoun_swap"

    def __init__(self, swap_titles: bool = True):
        self.swap_titles = swap_titles

    def replacements(self, doc, gender: str = "", key: str = "") -> list[Replacement]:
        out = []
        for tok in doc:
            low = tok.text.lower()
            if low == "her":
                tgt = her_target(tok)
            elif low == "his":
                tgt = his_target(tok)
            elif low in SIMPLE:
                if low.rstrip(".") in ("mr", "ms", "mrs", "miss"):
                    if not self.swap_titles or not tok.is_title and not tok.is_upper:
                        continue  # 'miss' as a verb, lower-case 'ms' (manuscript) etc.
                tgt = SIMPLE[low]
            else:
                continue
            out.append(Replacement(tok.i, tok.i + 1, match_case(tok.text, tgt), "pronoun", f"{low}->{tgt}"))
        return out
