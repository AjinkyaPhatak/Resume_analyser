"""Fairness metrics: counterfactual score gaps, rank shifts, TPR gender gap, exposure.

Orientation of signed quantities: every perturbed bio carries ``sign`` in {+1, -1} so
that  sign * (s(perturbed) - s(original))  is the score of the FEMALE-coded (or communal,
or target) version minus the other version. Positive = the scorer favours the female /
communal / target version. (For a male bio turned female, sign = +1; for a female bio
turned male, sign = -1.)

Scale: scorers' raw scores aren't comparable (BM25 is unbounded, cosines lie in [-1, 1]),
so the primary gap is NORMALISED by the standard deviation of the original scores in
the same pool (the JD's 100 candidates): |delta| / sd_pool. Raw gaps are reported too.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .ranking import expected_position_weights


def _rank_against(others_sorted: np.ndarray, v: float) -> float:
    """Expected 1-based rank of a value v among ``others`` (descending; ties count half)."""
    n = len(others_sorted)
    lo = np.searchsorted(others_sorted, v, side="left")
    hi = np.searchsorted(others_sorted, v, side="right")
    greater = n - hi
    ties = hi - lo
    return 1.0 + greater + ties / 2.0


def pool_counterfactual(orig_scores: np.ndarray, pert_scores: np.ndarray, sign: np.ndarray,
                        changed: np.ndarray) -> dict[str, float]:
    """Per-pool gap and rank-shift statistics for one condition.

    All arrays are aligned over the pool's bios. Unchanged bios have pert == orig.
    Returns means over all bios and over changed bios (NaN if none changed).
    """
    orig = np.asarray(orig_scores, float)
    pert = np.asarray(pert_scores, float)
    sign = np.asarray(sign, float)
    changed = np.asarray(changed, bool)
    sd = float(orig.std(ddof=1)) if len(orig) > 1 else float("nan")
    delta = pert - orig
    fav = sign * delta                         # >0: female/communal/target version scores higher

    rank_orig = np.empty(len(orig))
    rank_pert = np.empty(len(orig))
    for i in range(len(orig)):
        others = np.sort(np.delete(orig, i))
        rank_orig[i] = _rank_against(others, orig[i])
        rank_pert[i] = _rank_against(others, pert[i])
    rank_fav = sign * (rank_orig - rank_pert)  # >0: female/communal version ranks higher

    def stats(mask, suffix):
        if not mask.any():
            return {f"{k}{suffix}": float("nan") for k in
                    ("abs_gap", "signed_gap", "abs_gap_norm", "signed_gap_norm", "abs_rank_shift", "signed_rank_shift")}
        return {
            f"abs_gap{suffix}": float(np.abs(delta[mask]).mean()),
            f"signed_gap{suffix}": float(fav[mask].mean()),
            f"abs_gap_norm{suffix}": float(np.abs(delta[mask]).mean() / sd) if sd > 0 else float("nan"),
            f"signed_gap_norm{suffix}": float(fav[mask].mean() / sd) if sd > 0 else float("nan"),
            f"abs_rank_shift{suffix}": float(np.abs(rank_orig[mask] - rank_pert[mask]).mean()),
            f"signed_rank_shift{suffix}": float(rank_fav[mask].mean()),
        }

    out = {"n_bios": int(len(orig)), "n_changed": int(changed.sum()), "pool_sd": sd}
    out.update(stats(np.ones(len(orig), bool), ""))
    out.update(stats(changed, "_changed"))
    return out


def pool_zscores(df: pd.DataFrame, score_col: str = "score", pool_col: str = "jd_id") -> pd.Series:
    g = df.groupby(pool_col)[score_col]
    sd = g.transform(lambda s: s.std(ddof=1))
    return (df[score_col] - g.transform("mean")) / sd.replace(0, np.nan)


def best_f1_threshold(z: np.ndarray, rel: np.ndarray, n_grid: int = 200) -> float:
    """Threshold on (per-pool z-scored) scores maximising F1 for binary relevance."""
    z = np.asarray(z, float)
    rel = np.asarray(rel, bool)
    keep = ~np.isnan(z)
    z, rel = z[keep], rel[keep]
    cands = np.unique(np.quantile(z, np.linspace(0, 1, n_grid)))
    best_t, best_f1 = float(cands[0]), -1.0
    for t in cands:
        pred = z >= t
        tp = (pred & rel).sum()
        if tp == 0:
            continue
        p, r = tp / pred.sum(), tp / rel.sum()
        f1 = 2 * p * r / (p + r)
        if f1 > best_f1:
            best_t, best_f1 = float(t), f1
    return best_t


def tpr_gender_gap(df: pd.DataFrame, threshold: float, z_col: str = "z") -> dict:
    """De-Arteaga et al. (2019)-style TPR gap among RELEVANT pairs, per JD occupation.

    'Positive' = shortlisted (z >= threshold). TPR_g = P(shortlisted | relevant, gender g).
    gap_o = TPR_F - TPR_M for occupation o. Returns per-occupation gaps, their mean and
    root-mean-square (RMS).
    """
    rel = df[df["rel_binary"] == 1]
    per = {}
    for occ, g in rel.groupby("jd_occupation"):
        tpr = {s: float((g.loc[g["bio_gender"] == s, z_col] >= threshold).mean())
               for s in ("F", "M") if (g["bio_gender"] == s).any()}
        if len(tpr) == 2:
            per[occ] = tpr["F"] - tpr["M"]
    vals = np.array(list(per.values()))
    return {"per_occupation": per,
            "mean": float(vals.mean()) if len(vals) else float("nan"),
            "rms": float(np.sqrt((vals ** 2).mean())) if len(vals) else float("nan")}


def pool_exposure(scores: np.ndarray, genders: np.ndarray, k: int = 10) -> dict[str, float]:
    """Female share of top-k (tie-aware) minus 0.5, plain and position-discounted.

    Pools are 50/50 by gender by construction, so 0 = parity; >0 = women over-exposed.
    """
    genders = np.asarray(genders)
    is_f = genders == "F"
    incl = expected_position_weights(scores, lambda p: 1.0 if p <= k else 0.0)
    disc = expected_position_weights(scores, lambda p: 1.0 / np.log2(p + 1) if p <= k else 0.0)
    return {f"topk_female_share_minus_half": float(incl[is_f].sum() / incl.sum() - 0.5),
            f"exposure_female_share_minus_half": float(disc[is_f].sum() / disc.sum() - 0.5)}
