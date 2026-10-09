"""Uncertainty and significance, with JD pools as the resampling unit.

Pairs within one pool (same JD) are not independent, so every CI is a CLUSTER bootstrap
over pools, and every comparison is a paired test over pools.

* bootstrap_ci: percentile CI of any statistic of a set of units (default: their mean);
  ``method="basic"`` gives the basic (reverse-percentile) interval [2t - q_hi, 2t - q_lo],
  used for statistics whose bootstrap distribution is shifted (e.g. an RMS of gaps,
  which resampling inflates, so percentile intervals can exclude the point estimate).
* paired_permutation_test: sign-flip test on per-pool differences between two scorers.
* holm: Holm-Bonferroni adjustment across a family of tests.
All randomness comes from seeded numpy Generators.
"""

from __future__ import annotations

from typing import Callable

import numpy as np


def bootstrap_ci(values: np.ndarray | None = None, n_units: int | None = None,
                 stat_fn: Callable[[np.ndarray], float] | None = None, n_boot: int = 1000,
                 alpha: float = 0.05, seed: int = 0, method: str = "percentile") -> tuple[float, float, float]:
    """Return (point estimate, ci_low, ci_high).

    Either pass ``values`` (one number per unit; statistic = nanmean), or ``n_units`` and
    ``stat_fn(unit_indices) -> float`` for statistics that must be recomputed from the
    resampled units (e.g. TPR gaps).
    """
    if values is not None:
        vals = np.asarray(values, float)
        vals = vals[~np.isnan(vals)]
        if len(vals) == 0:
            return float("nan"), float("nan"), float("nan")
        rng = np.random.default_rng(seed)
        boots = vals[rng.integers(0, len(vals), (n_boot, len(vals)))].mean(axis=1)   # vectorised
        lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
        return float(vals.mean()), float(lo), float(hi)
    if stat_fn is None or not n_units:
        raise ValueError("need values, or n_units and stat_fn")
    rng = np.random.default_rng(seed)
    point = stat_fn(np.arange(n_units))
    boots = np.array([stat_fn(rng.integers(0, n_units, n_units)) for _ in range(n_boot)], float)
    boots = boots[~np.isnan(boots)]
    if len(boots) == 0:
        return point, float("nan"), float("nan")
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    if method == "basic":
        lo, hi = 2 * point - hi, 2 * point - lo
    elif method != "percentile":
        raise ValueError("method must be 'percentile' or 'basic'")
    return float(point), float(lo), float(hi)


def paired_permutation_test(a: np.ndarray, b: np.ndarray, n_perm: int = 10000, seed: int = 0) -> dict:
    """Two-sided sign-flip test of mean(a - b) = 0 over paired units (NaN pairs dropped)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    keep = ~(np.isnan(a) | np.isnan(b))
    d = a[keep] - b[keep]
    if len(d) == 0:
        return {"mean_diff": float("nan"), "p_value": float("nan"), "n_units": 0}
    obs = abs(d.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(d)))
    null = np.abs((signs * d).mean(axis=1))
    p = (1 + int((null >= obs - 1e-15).sum())) / (1 + n_perm)
    return {"mean_diff": float(d.mean()), "p_value": float(p), "n_units": int(len(d))}


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (NaNs passed through)."""
    p = np.asarray(pvalues, float)
    out = np.full(len(p), np.nan)
    idx = np.where(~np.isnan(p))[0]
    order = idx[np.argsort(p[idx])]
    m = len(order)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out.tolist()
