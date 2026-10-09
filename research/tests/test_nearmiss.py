"""Near-miss sweep helpers on toy data."""

import numpy as np
import pandas as pd
import pytest

from research.experiments.nearmiss_sweep import band_ci, band_table, grid, related

PARENTS = {"a": {"P"}, "b": {"P"}, "c": {"Q"}, "P": {"ROOT"}}


@pytest.mark.parametrize("x, y, strict, lenient", [
    ("a", "a", True, True),        # same concept
    ("a", "P", True, True),        # direct parent
    ("P", "a", True, True),        # direct child
    ("a", "b", False, True),       # siblings
    ("a", "c", False, False),      # unrelated
    ("a", "ROOT", False, False),   # grandparent: not adjacent
])
def test_related(x, y, strict, lenient):
    assert related(x, y, PARENTS, lenient=False) is strict
    assert related(x, y, PARENTS, lenient=True) is lenient


def _matches():
    return pd.DataFrame({"jd_id": ["j1", "j1", "j2", "j2"], "bio_id": ["b1", "b1", "b2", "b2"],
                         "sim": [0.40, 0.50, 0.60, 0.30], "strict": [True, False, True, False],
                         "lenient": [True, True, True, False]})


def test_band_table():
    t = band_table(_matches(), grid([0.35, 0.35, 0.05]), grid([0.55, 0.55, 0.05])).iloc[0]
    assert (t["lo"], t["hi"], t["n"]) == (0.35, 0.55, 2)
    assert t["strict"] == 0.5 and t["lenient"] == 1.0 and t["per_pair"] == 1.0


def test_band_ci_and_empty():
    (p, lo, hi), n = band_ci(_matches(), 0.35, 0.55, "strict", n_boot=50, seed=0)
    assert n == 2 and p == 0.5 and lo <= p <= hi
    (p2, _, _), n2 = band_ci(_matches(), 0.95, 0.99, "strict", n_boot=10, seed=0)
    assert n2 == 0 and np.isnan(p2)


def test_grid_inclusive():
    np.testing.assert_allclose(grid([0.2, 0.3, 0.05]), [0.2, 0.25, 0.3])
