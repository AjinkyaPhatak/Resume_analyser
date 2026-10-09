"""Lexical baselines: BM25 (keyword ATS stand-in) and TF-IDF cosine.

Both are fitted on a corpus (IDF statistics) and then score any (resume, jd) pair,
including perturbed resumes that weren't in the corpus, so the IDF is identical for an
original resume and its counterfactual.

Tokenisation: lower-case, alphanumeric tokens (keeping '+', '#' inside tokens, so 'c++'
and 'c#' survive), and optionally sklearn's English stop words removed. NB: that stop-word
list contains he/she/his/her/him, so with stop words on, pronoun swaps can't move these
scores at all. That's realistic for keyword ATSs and is reported as such.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Sequence

import numpy as np

from .base import BaseScorer

_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#]*")


def make_tokenizer(remove_stopwords: bool = True):
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    stop = ENGLISH_STOP_WORDS if remove_stopwords else frozenset()

    def tokenize(text: str) -> list[str]:
        return [t for t in _TOKEN.findall(text.lower()) if t not in stop]

    return tokenize


class BM25Scorer(BaseScorer):
    """Okapi BM25 with the exact formula of ``rank_bm25.BM25Okapi`` (v0.2.2).

    query = JD tokens, document = resume tokens.
      idf(t) = ln(N - n_t + 0.5) - ln(n_t + 0.5); negative idf -> epsilon * mean idf
      score  = sum over query tokens (with repeats) of
               idf(t) * f(t,d) * (k1 + 1) / (f(t,d) + k1 * (1 - b + b * |d| / avgdl))
    Query tokens unseen in the fitted corpus contribute 0 (as in rank_bm25).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25,
                 remove_stopwords: bool = True, name: str = "bm25"):
        self.name = name
        self.k1, self.b, self.epsilon = k1, b, epsilon
        self.tokenize = make_tokenizer(remove_stopwords)
        self.idf: dict[str, float] | None = None
        self.avgdl: float | None = None

    def fit(self, corpus: Sequence[str]) -> "BM25Scorer":
        docs = [self.tokenize(t) for t in corpus]
        n = len(docs)
        if n == 0:
            raise ValueError("empty corpus")
        df = Counter(t for d in docs for t in set(d))
        self.avgdl = sum(len(d) for d in docs) / n
        idf = {t: math.log(n - c + 0.5) - math.log(c + 0.5) for t, c in df.items()}
        avg_idf = sum(idf.values()) / len(idf)
        eps = self.epsilon * avg_idf
        self.idf = {t: (v if v >= 0 else eps) for t, v in idf.items()}
        return self

    def _score_tokens(self, doc: list[str], query: list[str]) -> float:
        if self.idf is None:
            raise RuntimeError("BM25Scorer.fit(corpus) must be called first")
        freqs = Counter(doc)
        norm = self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl)
        s = 0.0
        for q in query:
            f = freqs.get(q, 0)
            if f:
                s += (self.idf.get(q) or 0.0) * f * (self.k1 + 1) / (f + norm)
        return s

    def score(self, resume: str, jd: str) -> float:
        return self._score_tokens(self.tokenize(resume), self.tokenize(jd))

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        cache: dict[str, list[str]] = {}
        tok = lambda t: cache.setdefault(t, self.tokenize(t))  # noqa: E731
        return [self._score_tokens(tok(r), tok(j)) for r, j in pairs]


class TfidfScorer(BaseScorer):
    """Cosine similarity of L2-normalised TF-IDF vectors (sklearn), fitted on a corpus."""

    def __init__(self, sublinear_tf: bool = True, min_df: int = 1, remove_stopwords: bool = True,
                 name: str = "tfidf"):
        self.name = name
        self.sublinear_tf, self.min_df = sublinear_tf, min_df
        self.tokenize = make_tokenizer(remove_stopwords)
        self.vectorizer = None

    def fit(self, corpus: Sequence[str]) -> "TfidfScorer":
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(tokenizer=self.tokenize, lowercase=False, token_pattern=None,
                                          sublinear_tf=self.sublinear_tf, min_df=self.min_df, norm="l2")
        self.vectorizer.fit(list(corpus))
        return self

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        if self.vectorizer is None:
            raise RuntimeError("TfidfScorer.fit(corpus) must be called first")
        if not pairs:
            return []
        texts = list(dict.fromkeys(t for p in pairs for t in p))
        idx = {t: i for i, t in enumerate(texts)}
        m = self.vectorizer.transform(texts)
        r = m[[idx[p[0]] for p in pairs]]
        j = m[[idx[p[1]] for p in pairs]]
        return np.asarray(r.multiply(j).sum(axis=1)).ravel().astype(float).tolist()

    def score(self, resume: str, jd: str) -> float:
        return self.score_batch([(resume, jd)])[0]
