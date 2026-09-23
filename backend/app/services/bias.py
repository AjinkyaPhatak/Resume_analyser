import re

# Based on Gaucher et al. (2011) and Bolukbasi et al. (2016)
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

def detect_bias(text: str) -> dict:
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    flagged = []

    for word in words:
        for m_word in MASCULINE_CODED:
            if word == m_word or word.startswith(m_word):
                flagged.append({
                    "word": word,
                    "type": "masculine-coded",
                    "source": "Gaucher et al. (2011)"
                })
                break
        for f_word in FEMININE_CODED:
            if word == f_word or word.startswith(f_word):
                flagged.append({
                    "word": word,
                    "type": "feminine-coded",
                    "source": "Gaucher et al. (2011)"
                })
                break

    masculine_count = sum(1 for f in flagged if f["type"] == "masculine-coded")
    feminine_count = sum(1 for f in flagged if f["type"] == "feminine-coded")
    total = len(flagged)

    # bias score: 0 = neutral, positive = masculine leaning, negative = feminine leaning
    bias_score = round((masculine_count - feminine_count) / max(len(words), 1) * 100, 2)

    if total == 0:
        verdict = "No significant bias detected"
    elif abs(bias_score) < 1:
        verdict = "Slightly biased — mostly balanced language"
    elif bias_score > 1:
        verdict = "Masculine-coded language detected — may discourage some applicants"
    else:
        verdict = "Feminine-coded language detected — may discourage some applicants"

    return {
        "bias_score": bias_score,
        "flagged_words": flagged,
        "verdict": verdict
    }