"""Figure and LaTeX-table generation on a toy metrics table (no real results)."""

import pandas as pd
import pytest

from research.analysis.figures import family_of, headline_scatter, metric_row, perturbation_bars
from research.analysis.tables import ci, esc, extraction_table, main_tables, selection_table

ACFG = {
    "our_method": "ours",
    "headline": {"x_metric": "ndcg@10", "y_condition": "gender_full", "y_metric": "abs_gap_norm_changed"},
    "bar_conditions": ["pronoun_swap", "gender_full"],
    "families": {"ours": ["ours"], "neural": ["dense"], "lexical": ["bm25"], "deployed": []},
    "display": {"ours": "Ours", "dense": "Dense", "bm25": "BM25"},
    "condition_display": {"pronoun_swap": "Pronoun", "gender_full": "Full flip", "name_swap_us": "Name (US)",
                          "agentic_communal": "Agentic"},
}


def toy_metrics():
    rows = []
    for s, nd, gap in (("ours", 0.5, 0.05), ("dense", 0.6, 0.2), ("bm25", 0.55, 0.0)):
        rows.append({"scorer": s, "split": "test", "condition": "original", "metric": "ndcg@10",
                     "value": nd, "ci_low": nd - 0.02, "ci_high": nd + 0.02, "n_units": 10})
        for c in ("pronoun_swap", "gender_full"):
            for m in ("abs_gap_norm_changed", "signed_gap_norm_changed"):
                rows.append({"scorer": s, "split": "test", "condition": c, "metric": m,
                             "value": gap, "ci_low": gap * 0.9, "ci_high": gap * 1.1, "n_units": 10})
    return pd.DataFrame(rows)


def test_metric_row_and_family():
    m = toy_metrics()
    assert metric_row(m, "dense", "original", "ndcg@10") == (0.6, pytest.approx(0.58), pytest.approx(0.62))
    assert all(pd.isna(v) for v in metric_row(m, "dense", "nope", "ndcg@10"))
    assert family_of("bm25", ACFG["families"]) == "lexical"


def test_figures_written(tmp_path):
    pts = headline_scatter(toy_metrics(), ACFG, tmp_path / "h", preliminary=True)
    assert set(pts.scorer) == {"ours", "dense", "bm25"}
    perturbation_bars(toy_metrics(), ACFG, tmp_path / "b")
    for base in ("h", "b"):
        assert (tmp_path / f"{base}.pdf").stat().st_size > 0 and (tmp_path / f"{base}.png").stat().st_size > 0


def test_latex_helpers():
    assert esc("a_b & 50%") == r"a\_b \& 50\%"
    assert ci(0.5, 0.4, 0.6) == r"0.500\,{\scriptsize[0.400, 0.600]}"
    assert ci(float("nan"), 0, 1) == "--"


def test_main_tables_with_significance():
    tests = pd.DataFrame({"condition": ["original", "gender_full"], "metric": ["ndcg@10", "abs_gap_norm_changed"],
                          "baseline": ["dense", "dense"], "p_holm": [0.001, 0.5]})
    tex = main_tables(toy_metrics(), tests, ACFG, preliminary=False)
    assert tex.count("\\begin{table*}") == 3 and "\\toprule" in tex and "\\bottomrule" in tex
    assert "\\textbf{Ours}" in tex
    dense_acc = next(l for l in tex.splitlines() if l.startswith("Dense") and "dagger" in l)
    assert "0.600" in dense_acc


def test_extraction_and_selection_tables(tmp_path):
    rows = []
    for ex in ("esco", "jobbert_ft_s1", "jobbert_ft_s2"):
        for mode, f1 in (("exact", 0.2), ("partial", 0.4)):
            rows.append({"extractor": ex, "split": "test", "group": "all", "view": "all", "mode": mode,
                         "precision": f1, "recall": f1, "f1": f1 + (0.01 if ex.endswith("2") else 0), "n_pred": 1, "n_gold": 1})
    p = tmp_path / "m.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    tex = extraction_table(p)
    assert "esco" in tex and "2 seeds" in tex and "$\\pm$" in tex
    sel = tmp_path / "sel"
    sel.mkdir()
    pd.DataFrame({"scorer": ["a", "b"], "split": "dev", "condition": "original", "metric": "ndcg@10",
                  "value": [0.5, 0.6], "ci_low": [0.4, 0.5], "ci_high": [0.6, 0.7]}).to_csv(sel / "metrics.csv", index=False)
    st = selection_table(sel, "b")
    assert st.index("b (selected)") < st.index("a &")
