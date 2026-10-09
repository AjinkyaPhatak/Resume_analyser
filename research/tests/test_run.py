"""Harness logic on a toy dataset with a fake scorer (no models, no real data)."""

import json

import numpy as np
import pandas as pd
import pytest

from research.experiments.run import (
    build_pair_table, orientation_sign, per_pool_metrics, score_split, significance, summarise, tpr_gap_with_ci,
)
from research.scorers.base import BaseScorer

ORIENT = {"default": "gender", "agentic_communal": "communal", "name_in_same_gender": "target"}


class CountScorer(BaseScorer):
    """Score = number of times 'nurse' occurs in the resume, plus a bonus for 'she'."""

    name = "count"

    def __init__(self, she_bonus=0.0):
        self.she_bonus = she_bonus

    def score(self, resume, jd):
        w = resume.lower().split()
        return w.count("nurse") + self.she_bonus * w.count("she")


def toy(n_pools=4):
    pools, bios, pert = [], {}, []
    for p in range(n_pools):
        for i, (g, occ) in enumerate([("F", "nurse"), ("M", "nurse"), ("F", "teacher"), ("M", "teacher")]):
            bid = f"b{p}_{i}"
            pron = "she" if g == "F" else "he"
            bios[bid] = f"{pron} is a {'nurse nurse' if occ == 'nurse' else 'teacher'} {i}"
            pools.append({"jd_id": f"j{p}", "jd_occupation": "nurse", "bio_id": bid, "bio_occupation": occ,
                          "bio_gender": g, "rel_binary": int(occ == "nurse"), "rel_graded": 2 if occ == "nurse" else 0})
            swapped = bios[bid].replace("she", "XX").replace("he", "she").replace("XX", "he")
            pert.append({"bio_id": bid, "condition": "pronoun_swap", "text": swapped, "changed": True,
                         "n_changes": 1, "changes": json.dumps([{"kind": "pronoun"}])})
            pert.append({"bio_id": bid, "condition": "affiliation_swap", "text": bios[bid], "changed": False,
                         "n_changes": 0, "changes": "[]"})
    return pd.DataFrame(pools), pd.Series(bios), pd.DataFrame(pert), pd.Series({f"j{p}": "nurse job" for p in range(n_pools)})


def test_orientation_sign():
    assert orientation_sign("pronoun_swap", "M", "[]", ORIENT) == 1
    assert orientation_sign("pronoun_swap", "F", "[]", ORIENT) == -1
    ch = json.dumps([{"kind": "communal->agentic"}, {"kind": "communal->agentic"}, {"kind": "agentic->communal"}])
    assert orientation_sign("agentic_communal", "F", ch, ORIENT) == -1
    assert orientation_sign("name_in_same_gender", "F", "[]", ORIENT) == 1


def test_build_pair_table_requires_counterfactuals():
    pools, bios, pert, jds = toy(1)
    with pytest.raises(ValueError):
        build_pair_table(pools, pert[pert["bio_id"] != "b0_0"], ["pronoun_swap"], ORIENT)


def _run(she_bonus):
    pools, bios, pert, jds = toy()
    table = build_pair_table(pools, pert, ["pronoun_swap", "affiliation_swap"], ORIENT)
    scored = score_split(CountScorer(she_bonus), table, bios, jds, chunk=5)
    return pools, scored, per_pool_metrics(scored, pools, ["pronoun_swap", "affiliation_swap"], exposure_k=2)


def test_unbiased_scorer_has_zero_gap_and_perfect_ranking():
    pools, scored, pp = _run(0.0)
    orig = pp[pp.condition == "original"]
    assert (orig["ndcg@10"] == 1.0).all() and (orig["mrr"] == 1.0).all()
    pron = pp[pp.condition == "pronoun_swap"]
    assert (pron["abs_gap"] == 0).all() and (pron["n_changed"] == 4).all()
    aff = pp[pp.condition == "affiliation_swap"]
    assert (aff["n_changed"] == 0).all() and aff["abs_gap_changed"].isna().all()


def test_biased_scorer_shows_signed_gap_towards_women():
    _, scored, pp = _run(0.5)
    pron = pp[pp.condition == "pronoun_swap"]
    # every swap moves 0.5 towards whoever now has "she" -> favours female version by 0.5 raw
    assert np.allclose(pron["signed_gap_changed"], 0.5)
    assert np.allclose(pron["abs_gap_changed"], 0.5)
    assert (pron["signed_gap_norm_changed"] > 0).all()
    # unchanged counterfactuals copy the original score exactly
    aff = scored[scored.condition == "affiliation_swap"].set_index(["jd_id", "bio_id"])["score"]
    orig = scored[scored.condition == "original"].set_index(["jd_id", "bio_id"])["score"]
    pd.testing.assert_series_equal(aff, orig.reindex(aff.index), check_names=False)


def test_summary_tests_and_tpr():
    pools, scored_b, pp_b = _run(0.5)
    _, scored_u, pp_u = _run(0.0)
    per_pool = pd.concat([pp_b.assign(scorer="biased", split="test"), pp_u.assign(scorer="fair", split="test")])
    m = summarise(per_pool, n_boot=200, alpha=0.05, seed=0)
    row = m[(m.scorer == "biased") & (m.condition == "pronoun_swap") & (m.metric == "abs_gap_changed")].iloc[0]
    assert row["value"] == pytest.approx(0.5) and row["n_units"] == 4
    t = significance(per_pool, "fair", ["pronoun_swap"], ["abs_gap_norm_changed"], n_perm=500, seed=0)
    r = t[(t.condition == "pronoun_swap")].iloc[0]
    assert r["baseline"] == "biased" and r["mean_diff"] < 0
    tpr = tpr_gap_with_ci(scored_u, scored_u, pools, pools, n_boot=100, alpha=0.05, seed=0)
    assert tpr["mean"][0] == pytest.approx(0.0)
