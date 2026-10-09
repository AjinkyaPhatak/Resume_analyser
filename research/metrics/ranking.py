"""Tie-aware ranking metrics for one pool (one JD and its candidate bios).

Several scorers produce many exact ties (e.g. the entity scorer gives 0.0 to bios with no
entities). Breaking ties arbitrarily would make metrics depend on input order, so every
metric here is the EXPECTED value over all orderings of tied items (McSherry & Najork,
2008, "Computing information retrieval performance measures efficiently in the presence
of tied scores", ECIR).

Ranks are 1-based; higher score = better rank.
"""

from __future__ import annotations

from math import comb, log2

import numpy as np


def tie_groups(scores: np.ndarray) -> list[tuple[int, np.ndarray]]:
    """[(first position (1-based), indices of items)] for groups of equal scores, best first."""
    scores = np.asarray(scores, dtype=float)
    if np.isnan(scores).any():
        raise ValueError("scores contain NaN")
    order = np.argsort(-scores, kind="stable")
    out, pos, i = [], 1, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        idx = order[i : j + 1]
        out.append((pos, idx))
        pos += len(idx)
        i = j + 1
    return out


def expected_ranks(scores: np.ndarray) -> np.ndarray:
    """Average position of each item over orderings of its tie group (like 'average' ranking)."""
    r = np.empty(len(scores), dtype=float)
    for start, idx in tie_groups(scores):
        r[idx] = start + (len(idx) - 1) / 2
    return r


def expected_position_weights(scores: np.ndarray, weight_fn) -> np.ndarray:
    """E[weight_fn(position)] for each item, averaging over its tie group's positions."""
    w = np.empty(len(scores), dtype=float)
    for start, idx in tie_groups(scores):
        w[idx] = np.mean([weight_fn(p) for p in range(start, start + len(idx))])
    return w


def _dcg_weight(k: int):
    return lambda p: 1.0 / log2(p + 1) if p <= k else 0.0


def ndcg_at_k(scores, gains, k: int = 10) -> float:
    """Tie-aware nDCG@k with exponential gain 2^g - 1 (g = graded relevance)."""
    gains = np.asarray(gains, dtype=float)
    g = 2.0 ** gains - 1.0
    ideal = np.sort(g)[::-1][:k]
    idcg = float(sum(v / log2(i + 2) for i, v in enumerate(ideal)))
    if idcg == 0:
        return float("nan")
    return float((g * expected_position_weights(scores, _dcg_weight(k))).sum() / idcg)


def precision_at_k(scores, rel, k: int) -> float:
    """Tie-aware P@k for binary relevance."""
    rel = np.asarray(rel, dtype=float)
    inclusion = expected_position_weights(scores, lambda p: 1.0 if p <= k else 0.0)
    return float((rel * inclusion).sum() / k)


def reciprocal_rank(scores, rel) -> float:
    """Tie-aware reciprocal rank of the first relevant item (binary relevance)."""
    rel = np.asarray(rel, dtype=bool)
    for start, idx in tie_groups(scores):
        r = int(rel[idx].sum())
        if r == 0:
            continue
        g = len(idx)
        # first relevant item lands at offset j (1-based) within the group with prob C(g-j, r-1)/C(g, r)
        total = comb(g, r)
        return float(sum(comb(g - j, r - 1) / total / (start + j - 1) for j in range(1, g - r + 2)))
    return 0.0


def pool_ranking_metrics(scores, rel_binary, rel_graded, ks=(5, 10)) -> dict[str, float]:
    out = {"ndcg@10": ndcg_at_k(scores, rel_graded, 10),
           "ndcg@10_binary": ndcg_at_k(scores, rel_binary, 10),
           "mrr": reciprocal_rank(scores, rel_binary)}
    for k in ks:
        out[f"p@{k}"] = precision_at_k(scores, rel_binary, k)
    return out
