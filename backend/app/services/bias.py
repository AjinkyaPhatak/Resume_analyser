"""Gender-coded wording check for job descriptions and resumes.

The word lists are adapted from Gaucher, Friesen & Kay (2011), "Evidence that gendered
wording in job advertisements exists and sustains gender inequality". Some entries come
from later practitioner lists, and the lists have NOT yet been checked word-by-word
against the paper's appendix (see research/BACKEND_AUDIT.md), which the response says.

Fixes from the Phase 0 audit:
  * hyphenated words ("self-reliant") are kept as one token, so they can match;
  * an entry matches the word itself or a simple inflection (-s, -ed, -ing, ...), not any
    word that merely starts with it ("kind" no longer flags "kindergarten");
  * the verdict uses symmetric cut-offs (a score of exactly +1 used to read "feminine").
"""

import re

MASCULINE_CODED = [
    "aggressive", "ambitious", "analytical", "assertive", "autonomous",
    "battle", "boast", "challenge", "champion", "competitive", "confident",
    "courageous", "decisive", "determined", "dominant", "driven",
    "fearless", "fighter", "forceful", "headstrong", "hierarchical",
    "hostile", "independent", "individual", "lead", "logic", "ninja",
    "objective", "outspoken", "persistent", "principled", "rockstar",
    "self-reliant", "self-sufficient", "stubborn", "superior", "warrior"
]

FEMININE_CODED = [
    "affectionate", "child", "cheer", "collaborate", "commit",
    "communal", "compassionate", "connect", "considerate", "cooperative",
    "dependable", "emotional", "empathy", "enthusiastic", "family",
    "flexible", "gentle", "honest", "interpersonal", "kind",
    "loyal", "nurturing", "patience", "pleasant", "polite",
    "responsive", "sensitive", "support", "sympathetic", "tender",
    "together", "trust", "understand", "warm", "yielding"
]

SOURCE = "Adapted from Gaucher et al. (2011); list not yet verified against the paper"
# what may follow an entry (minus a final "e"): inflections and close derivations only
_ENDINGS = {"", "e", "s", "es", "d", "ed", "ing", "er", "ers", "ly", "ive", "ted", "ting",
            "ment", "ments", "ion", "ions"}
_WORD = re.compile(r"[a-z]+(?:-[a-z]+)*")
VERDICT_CUTOFF = 1.0     # coded words per 100 words


def _lookup(word: str, entries: list[str]) -> str | None:
    """The entry ``word`` is a form of: "leads"/"leader" -> lead, "collaborating" -> collaborate.

    Not a bare prefix match: "kindergarten", "committee", "trustee" are not flagged.
    """
    for e in entries:
        stem = e[:-1] if e.endswith("e") else e
        if word.startswith(stem) and word[len(stem):] in _ENDINGS:
            return e
    return None


def detect_bias(text: str) -> dict:
    words = _WORD.findall(text.lower())
    flagged = []
    for word in words:
        m = _lookup(word, MASCULINE_CODED)
        if m:
            flagged.append({"word": word, "type": "masculine-coded", "matched": m, "source": SOURCE})
        f = _lookup(word, FEMININE_CODED)
        if f:
            flagged.append({"word": word, "type": "feminine-coded", "matched": f, "source": SOURCE})

    masculine = sum(1 for x in flagged if x["type"] == "masculine-coded")
    feminine = sum(1 for x in flagged if x["type"] == "feminine-coded")
    # 0 = balanced, positive = masculine-leaning, negative = feminine-leaning (per 100 words)
    bias_score = round((masculine - feminine) / max(len(words), 1) * 100, 2)

    if not flagged:
        verdict = "No gender-coded words found"
    elif abs(bias_score) < VERDICT_CUTOFF:
        verdict = "Roughly balanced: masculine- and feminine-coded words appear at similar rates"
    elif bias_score > 0:
        verdict = "Leans masculine-coded: may discourage some applicants"
    else:
        verdict = "Leans feminine-coded: may discourage some applicants"

    return {"bias_score": bias_score, "flagged_words": flagged, "verdict": verdict,
            "masculine_count": masculine, "feminine_count": feminine, "n_words": len(words)}
