"""EntityLateInteractionScorer: our method.

Late interaction (cf. ColBERT, Khattab & Zaharia 2020; BERTScore, Zhang et al. 2020)
applied to *extracted skill entities* instead of all tokens:
  1. extract typed entity spans from the resume and the JD (any Extractor);
  2. keep the configured entity types (labels and/or sources);
  3. embed each distinct entity string on its own (cached sentence-transformer);
  4. build the JD x resume cosine-similarity matrix;
  5. aggregate (scorers/aggregation.py: maxsim_mean | idf_weighted | hungarian |
     threshold_fraction).
The hypothesis under test is that restricting the interaction to skill entities keeps
demographic cues (names, pronouns, gendered wording) out of the score. The mechanism
itself is not claimed as new.

With extractor=noun_chunk, dedupe=exact, backbone all-MiniLM-L6-v2 and
threshold_fraction@0.55, this reproduces the deployed backend's match_percent / 100.

If either side has no entities left after filtering, the score is 0.0 and the event is
counted in ``n_empty`` (reported with results, never hidden).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from research.extraction.base import TypedSpan

from .aggregation import aggregate, idf_table
from .base import BaseScorer


class EntityLateInteractionScorer(BaseScorer):
    def __init__(self, extractor, encoder, aggregation: str = "maxsim_mean",
                 labels: Sequence[str] | None = ("skill", "knowledge"),
                 sources: Sequence[str] | None = None, dedupe: str = "casefold",
                 threshold: float | None = None, name: str = "entity_li"):
        if dedupe not in ("exact", "casefold"):
            raise ValueError("dedupe must be 'exact' or 'casefold'")
        self.name = name
        self.extractor = extractor        # anything with extract_batch(texts) -> list[list[TypedSpan]]
        self.encoder = encoder            # anything with encode(list[str]) -> (n, d) L2-normalised
        self.aggregation = aggregation
        self.labels = set(labels) if labels else None
        self.sources = set(sources) if sources else None
        self.dedupe = dedupe
        self.threshold = threshold
        self.idf: dict[str, float] | None = None
        self.idf_unseen: float | None = None
        self.n_empty = 0

    # --- entities ------------------------------------------------------------------
    def _keep(self, s: TypedSpan) -> bool:
        return (self.labels is None or s.label in self.labels) and (self.sources is None or s.source in self.sources)

    def _key(self, text: str) -> str:
        return text.strip().lower() if self.dedupe == "casefold" else text.strip()

    def entities(self, spans: list[TypedSpan]) -> list[str]:
        """Distinct entity strings in first-occurrence order (first surface form kept)."""
        seen: dict[str, str] = {}
        for s in spans:
            t = s.text.strip()
            if t and self._keep(s):
                seen.setdefault(self._key(t), t)
        return list(seen.values())

    def entities_batch(self, texts: Sequence[str]) -> list[list[str]]:
        return [self.entities(sp) for sp in self.extractor.extract_batch(list(texts))]

    # --- fitting ---------------------------------------------------------------------
    def fit(self, jd_texts: Sequence[str]) -> "EntityLateInteractionScorer":
        """IDF of JD entities over a JD corpus (needed only for idf_weighted)."""
        sets = [{self._key(e) for e in ents} for ents in self.entities_batch(sorted(set(jd_texts)))]
        self.idf, self.idf_unseen = idf_table(sets)
        return self

    # --- scoring ---------------------------------------------------------------------
    def _score_from(self, r_ents: list[str], j_ents: list[str], vec: dict[str, np.ndarray]) -> float:
        if not r_ents or not j_ents:
            self.n_empty += 1
            return 0.0
        sim = np.stack([vec[e] for e in j_ents]) @ np.stack([vec[e] for e in r_ents]).T
        weights = None
        if self.aggregation == "idf_weighted":
            if self.idf is None:
                raise RuntimeError("idf_weighted needs fit(jd_texts) first")
            weights = np.array([self.idf.get(self._key(e), self.idf_unseen) for e in j_ents])
        return aggregate(sim, self.aggregation, weights=weights, threshold=self.threshold)

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        texts = list(dict.fromkeys(t for pair in pairs for t in pair))
        ents = dict(zip(texts, self.entities_batch(texts)))
        strings = sorted({e for es in ents.values() for e in es})
        vec = dict(zip(strings, self.encoder.encode(strings))) if strings else {}
        return [self._score_from(ents[r], ents[j], vec) for r, j in pairs]

    def score(self, resume: str, jd: str) -> float:
        return self.score_batch([(resume, jd)])[0]

    def explain(self, resume: str, jd: str) -> dict:
        """Entities, best matches and per-JD-entity max similarity, for inspection."""
        r_ents, j_ents = self.entities_batch([resume, jd])
        if not r_ents or not j_ents:
            return {"resume_entities": r_ents, "jd_entities": j_ents, "matches": []}
        vec = dict(zip(r_ents + j_ents, self.encoder.encode(r_ents + j_ents)))
        sim = np.stack([vec[e] for e in j_ents]) @ np.stack([vec[e] for e in r_ents]).T
        best = sim.argmax(axis=1)
        return {"resume_entities": r_ents, "jd_entities": j_ents,
                "matches": [(j_ents[i], r_ents[best[i]], float(sim[i, best[i]])) for i in range(len(j_ents))]}
