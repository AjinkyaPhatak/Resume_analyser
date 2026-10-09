"""Annotation sampling, storage and agreement on toy data."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import cohen_kappa_score

from research.annotation.agreement import kappas, krippendorff_ordinal, spearman_ci
from research.annotation.sample import allocate, consensus_scores, stratified_sample
from research.annotation.storage import (
    annotator_id, annotator_order, labels_path, load_all, load_ratings, save_rating,
)


# --- sampling ------------------------------------------------------------------------

def test_allocate_min_one_then_proportional():
    sizes = pd.Series({"a": 100, "b": 10, "c": 1, "d": 0})
    alloc = allocate(sizes, 20)
    assert alloc.sum() == 20 and "d" not in alloc.index
    assert (alloc >= 1).all() and alloc["a"] > alloc["b"] >= alloc["c"] == 1


def test_allocate_budget_smaller_than_strata():
    alloc = allocate(pd.Series({"a": 5, "b": 4, "c": 3}), 2)
    assert alloc.to_dict() == {"a": 1, "b": 1, "c": 0}


def test_allocate_respects_capacity():
    alloc = allocate(pd.Series({"a": 2, "b": 2}), 10)
    assert alloc.to_dict() == {"a": 2, "b": 2}


def test_stratified_sample_deterministic():
    frame = pd.DataFrame({"occ": ["x"] * 30 + ["y"] * 10, "g": ["F", "M"] * 20, "v": range(40)})
    a = stratified_sample(frame, ["occ", "g"], 8, np.random.default_rng(1))
    b = stratified_sample(frame, ["occ", "g"], 8, np.random.default_rng(1))
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 8 and set(a["occ"]) == {"x", "y"} and a["v"].is_unique


def test_consensus_scores():
    s = pd.DataFrame({"split": "test", "condition": "original", "scorer": ["a", "a", "b", "b"],
                      "jd_id": "j", "bio_id": ["x", "y", "x", "y"], "score": [1.0, 2.0, 5.0, 3.0]})
    c = consensus_scores(s, ["a", "b"], "test").set_index("bio_id")["consensus"]
    assert c["x"] == pytest.approx(0.75) and c["y"] == pytest.approx(0.75)
    with pytest.raises(ValueError):
        consensus_scores(s, ["a", "zzz"], "test")


# --- storage ---------------------------------------------------------------------------

def test_annotator_id():
    assert annotator_id("  Priya S. ") == "priya_s"
    with pytest.raises(ValueError):
        annotator_id("  ..  ")


def test_save_and_reload_latest_wins(tmp_path):
    p = labels_path(tmp_path, "Ann")
    save_rating(p, "p001", 2, "unsure")
    save_rating(p, "p002", 0)
    save_rating(p, "p001", 3, "changed my mind")
    r = load_ratings(p).set_index("pair_id")
    assert r.loc["p001", "rating"] == 3 and r.loc["p001", "comment"] == "changed my mind"
    assert len(pd.read_csv(p)) == 3                     # history kept
    with pytest.raises(ValueError):
        save_rating(p, "p003", 5)


def test_order_is_per_annotator_and_stable():
    ids = [f"p{i:03d}" for i in range(50)]
    assert annotator_order(ids, "Ann") == annotator_order(ids, "ann")
    assert annotator_order(ids, "Ann") != annotator_order(ids, "Bob")
    assert sorted(annotator_order(ids, "Ann")) == ids


def test_load_all_wide(tmp_path):
    save_rating(labels_path(tmp_path, "a"), "p1", 1)
    save_rating(labels_path(tmp_path, "b"), "p1", 2)
    save_rating(labels_path(tmp_path, "b"), "p2", 0)
    w = load_all(tmp_path)
    assert list(w.columns) == ["a", "b"] and np.isnan(w.loc["p2", "a"]) and w.loc["p1", "b"] == 2


# --- agreement -------------------------------------------------------------------------

def test_kappas_match_sklearn():
    w = pd.DataFrame({"a": [0, 1, 2, 3, 3, 2], "b": [0, 1, 2, 2, 3, 1]})
    k = kappas(w).iloc[0]
    assert k["kappa"] == pytest.approx(cohen_kappa_score(w.a, w.b))
    assert k["kappa_quadratic"] == pytest.approx(cohen_kappa_score(w.a, w.b, weights="quadratic"))


def test_krippendorff_perfect_and_missing():
    w = pd.DataFrame({"a": [0, 1, 2, 3], "b": [0, 1, 2, 3], "c": [0, 1, np.nan, 3]})
    assert krippendorff_ordinal(w) == pytest.approx(1.0)
    noisy = pd.DataFrame({"a": [0, 1, 2, 3, 0, 3], "b": [3, 0, 1, 0, 2, 1]})
    assert krippendorff_ordinal(noisy) < 0.2


def test_spearman_ci():
    x = np.arange(30.0)
    (rho, lo, hi), n = spearman_ci(x, x ** 2, n_boot=200, alpha=0.05, seed=0)
    assert rho == pytest.approx(1.0) and n == 30 and lo <= rho


# --- app (headless, via streamlit's AppTest) -----------------------------------------

def test_app_rates_and_saves(tmp_path, monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    sample = tmp_path / "sample.csv"
    pd.DataFrame({"pair_id": ["p000", "p001"], "jd_title": ["Nurse", "Paralegal"],
                  "jd_text": ["ICU nurse job", "Law firm"], "bio_text": ["She is a nurse.", "He paints."]}).to_csv(sample, index=False)
    cfg = tmp_path / "ann.yaml"
    cfg.write_text(f"annotation:\n  sample_csv: '{sample.as_posix()}'\n  labels_dir: '{(tmp_path / 'labels').as_posix()}'\n"
                   "  scale: [0, 1, 2, 3]\n", encoding="utf-8")
    monkeypatch.setenv("RESEARCH_ANNOTATION_CONFIG", str(cfg))
    app = Path(__file__).resolve().parents[1] / "annotation" / "app.py"

    at = AppTest.from_file(str(app), default_timeout=60).run()
    assert not at.exception
    assert "Enter your name" in at.info[0].value
    at.sidebar.text_input[0].set_value("Test Annotator").run()
    first = at.caption[-1].value
    from research.annotation.app import SCALE_HELP

    pid = first.split()[-1]
    at.radio(key=f"rating_{pid}").set_value(SCALE_HELP[3])   # no rerun before submit: forms commit on submit
    at.button[0].click().run()
    assert not at.exception
    saved = load_ratings(labels_path(tmp_path / "labels", "Test Annotator"))
    assert len(saved) == 1 and saved.loc[0, "rating"] == 3 and saved.loc[0, "pair_id"] in first
    assert at.caption[-1].value != first          # moved on to the next pair
