"""Ranking / fairness / statistics metrics against hand-computed values."""

from math import log2

import numpy as np
import pandas as pd
import pytest

from research.metrics.fairness import (
    best_f1_threshold, pool_counterfactual, pool_exposure, pool_zscores, tpr_gender_gap,
)
from research.metrics.ranking import (
    expected_ranks, ndcg_at_k, pool_ranking_metrics, precision_at_k, reciprocal_rank, tie_groups,
)
from research.metrics.stats import bootstrap_ci, holm, paired_permutation_test


# --- ranking ------------------------------------------------------------------------

def test_tie_groups_and_expected_ranks():
    s = np.array([0.5, 0.9, 0.5, 0.1])
    groups = tie_groups(s)
    assert [(start, sorted(idx.tolist())) for start, idx in groups] == [(1, [1]), (2, [0, 2]), (4, [3])]
    np.testing.assert_allclose(expected_ranks(s), [2.5, 1, 2.5, 4])


def test_nan_scores_rejected():
    with pytest.raises(ValueError):
        tie_groups(np.array([0.1, np.nan]))


def test_ndcg_perfect_and_worst():
    assert ndcg_at_k([3, 2, 1, 0], [2, 1, 0, 0], k=10) == pytest.approx(1.0)
    worst = ndcg_at_k([0, 1, 2, 3], [1, 0, 0, 0], k=10)
    assert worst == pytest.approx(1 / log2(5))


def test_ndcg_cutoff_and_no_relevant():
    assert ndcg_at_k([3, 2, 1], [0, 0, 1], k=2) == 0.0
    assert np.isnan(ndcg_at_k([1, 2], [0, 0]))


def test_ndcg_ties_are_averaged():
    # all tied, one relevant among 2: expected discount = mean(1/log2(2), 1/log2(3))
    v = ndcg_at_k([0.0, 0.0], [1, 0], k=10)
    assert v == pytest.approx((1 + 1 / log2(3)) / 2)


def test_precision_with_ties():
    # top-2 cutoff cuts a tie group of 2 at position 2..3 containing 1 relevant
    s = [0.9, 0.5, 0.5, 0.1]
    rel = [0, 1, 0, 0]
    assert precision_at_k(s, rel, 2) == pytest.approx(0.5 * 0.5)   # inclusion prob 1/2, /k
    assert precision_at_k(s, rel, 3) == pytest.approx(1 / 3)


def test_reciprocal_rank():
    assert reciprocal_rank([0.9, 0.5, 0.1], [0, 1, 0]) == pytest.approx(0.5)
    assert reciprocal_rank([0.0, 0.0], [1, 0]) == pytest.approx(0.75)          # tie of 2, 1 relevant
    assert reciprocal_rank([0.0, 0.0, 0.0], [1, 1, 0]) == pytest.approx(2 / 3 + 1 / 3 * 1 / 2)
    assert reciprocal_rank([0.3, 0.2], [0, 0]) == 0.0


def test_pool_ranking_metrics_keys():
    m = pool_ranking_metrics([3, 2, 1, 0], [1, 0, 0, 0], [2, 1, 0, 0])
    assert set(m) == {"ndcg@10", "ndcg@10_binary", "mrr", "p@5", "p@10"}
    assert m["mrr"] == 1.0 and m["p@5"] == pytest.approx(0.2)


# --- fairness ----------------------------------------------------------------------

def test_pool_counterfactual_gap_and_rank():
    orig = np.array([1.0, 2.0, 3.0, 4.0])
    pert = np.array([1.0, 2.0, 3.0, 2.5])     # only bio 3 changes: drops from rank 1 to rank 2
    sign = np.array([1, 1, 1, -1])            # bio 3 was female -> male version => favour F = +1.5
    changed = np.array([False, False, False, True])
    m = pool_counterfactual(orig, pert, sign, changed)
    sd = orig.std(ddof=1)
    assert m["abs_gap"] == pytest.approx(1.5 / 4)
    assert m["abs_gap_changed"] == pytest.approx(1.5)
    assert m["signed_gap_changed"] == pytest.approx(1.5)
    assert m["abs_gap_norm_changed"] == pytest.approx(1.5 / sd)
    assert m["abs_rank_shift_changed"] == pytest.approx(1.0)
    assert m["signed_rank_shift_changed"] == pytest.approx(1.0)   # female version ranked higher
    assert m["n_changed"] == 1


def test_pool_counterfactual_nothing_changed():
    m = pool_counterfactual(np.array([1.0, 2.0]), np.array([1.0, 2.0]), np.array([1, 1]), np.array([False, False]))
    assert m["abs_gap"] == 0.0 and np.isnan(m["abs_gap_changed"])


def test_zscores_and_threshold():
    df = pd.DataFrame({"jd_id": ["a"] * 4 + ["b"] * 4, "score": [1, 2, 3, 4, 10, 20, 30, 40]})
    z = pool_zscores(df)
    np.testing.assert_allclose(z[:4], z[4:])
    t = best_f1_threshold(np.array([-1, -0.5, 0.5, 1.0]), np.array([0, 0, 1, 1]))
    assert -0.5 < t <= 0.5


def test_tpr_gap():
    df = pd.DataFrame({
        "rel_binary": [1, 1, 1, 1, 0],
        "jd_occupation": ["nurse"] * 5,
        "bio_gender": ["F", "F", "M", "M", "F"],
        "z": [1.0, 1.0, 1.0, -1.0, 5.0],
    })
    out = tpr_gender_gap(df, threshold=0.0)
    assert out["per_occupation"]["nurse"] == pytest.approx(1.0 - 0.5)
    assert out["rms"] == pytest.approx(0.5)


def test_exposure_parity():
    scores = np.array([4, 3, 2, 1])
    assert pool_exposure(scores, np.array(["F", "M", "F", "M"]), k=4)["topk_female_share_minus_half"] == pytest.approx(0)
    e = pool_exposure(scores, np.array(["F", "F", "M", "M"]), k=2)
    assert e["topk_female_share_minus_half"] == pytest.approx(0.5)
    assert e["exposure_female_share_minus_half"] == pytest.approx(0.5)


# --- stats ---------------------------------------------------------------------------

def test_bootstrap_ci_reproducible_and_contains_mean():
    v = np.random.default_rng(0).normal(1.0, 1.0, 200)
    a = bootstrap_ci(v, seed=3)
    assert a == bootstrap_ci(v, seed=3)
    assert a[1] < v.mean() < a[2] and a[0] == pytest.approx(v.mean())


def test_bootstrap_custom_stat():
    v = np.arange(10.0)
    point, lo, hi = bootstrap_ci(n_units=10, stat_fn=lambda idx: float(np.median(v[idx])), seed=1)
    assert point == 4.5 and lo <= 4.5 <= hi


def test_bootstrap_all_nan():
    assert all(np.isnan(x) for x in bootstrap_ci(np.array([np.nan, np.nan])))


def test_permutation_test():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 50)
    assert paired_permutation_test(a + 1.0, a, n_perm=2000)["p_value"] < 0.01
    assert paired_permutation_test(a, a + rng.normal(0, 1e-9, 50), n_perm=2000)["p_value"] > 0.05


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    out = holm([0.01, float("nan")])
    assert out[0] == pytest.approx(0.01) and np.isnan(out[1])
