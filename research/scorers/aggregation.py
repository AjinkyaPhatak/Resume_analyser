"""Aggregations of a JD-entity x resume-entity similarity matrix into one score.

``sim`` has shape (n_jd, n_resume), cosine similarities. Every aggregation is
recall-oriented: it asks how well the resume covers the JD's entities. That's the late-
interaction pattern of ColBERT (Khattab & Zaharia, 2020) and BERTScore recall (Zhang et
al., 2020); we don't claim the mechanism is new.

* maxsim_mean:   mean_i max_j sim[i, j]               (BERTScore-recall / ColBERT MaxSim)
* idf_weighted:  sum_i w_i max_j sim[i, j], w = normalised IDF of JD entity i
* hungarian:     one-to-one optimal assignment (scipy linear_sum_assignment, maximising
                 total similarity); score = sum of assigned sims / n_jd, so JD entities
                 left unassigned (when n_resume < n_jd) contribute 0
* threshold_fraction: share of JD entities whose max similarity >= threshold
                 (the deployed backend's match_percent / 100 when threshold = 0.55)
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

AGGREGATIONS = ("maxsim_mean", "idf_weighted", "hungarian", "threshold_fraction")


def maxsim_mean(sim: np.ndarray) -> float:
    return float(sim.max(axis=1).mean())


def idf_weighted(sim: np.ndarray, weights: np.ndarray) -> float:
    w = np.asarray(weights, dtype=np.float64)
    if w.shape != (sim.shape[0],) or (w < 0).any() or w.sum() <= 0:
        raise ValueError("weights must be non-negative, one per JD entity, not all zero")
    return float((sim.max(axis=1) * (w / w.sum())).sum())


def hungarian(sim: np.ndarray) -> float:
    rows, cols = linear_sum_assignment(sim, maximize=True)
    return float(sim[rows, cols].sum() / sim.shape[0])


def threshold_fraction(sim: np.ndarray, threshold: float) -> float:
    return float((sim.max(axis=1) >= threshold).mean())


def aggregate(sim: np.ndarray, method: str, weights: np.ndarray | None = None,
              threshold: float | None = None) -> float:
    if sim.ndim != 2 or 0 in sim.shape:
        raise ValueError(f"need a non-empty 2-D matrix, got shape {sim.shape}")
    if method == "maxsim_mean":
        return maxsim_mean(sim)
    if method == "idf_weighted":
        if weights is None:
            raise ValueError("idf_weighted needs weights")
        return idf_weighted(sim, weights)
    if method == "hungarian":
        return hungarian(sim)
    if method == "threshold_fraction":
        if threshold is None:
            raise ValueError("threshold_fraction needs a threshold")
        return threshold_fraction(sim, threshold)
    raise ValueError(f"unknown aggregation {method!r}; expected one of {AGGREGATIONS}")


def idf_table(entity_sets: list[set[str]]) -> tuple[dict[str, float], float]:
    """Smoothed IDF over documents (each a set of normalised entity strings).

    idf(e) = ln((N + 1) / (df(e) + 1)) + 1. Returns (table, idf for unseen entities).
    """
    n = len(entity_sets)
    df: dict[str, int] = {}
    for s in entity_sets:
        for e in s:
            df[e] = df.get(e, 0) + 1
    table = {e: float(np.log((n + 1) / (c + 1)) + 1.0) for e, c in df.items()}
    return table, float(np.log(n + 1) + 1.0)
