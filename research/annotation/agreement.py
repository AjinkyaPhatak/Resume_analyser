"""Inter-annotator agreement and scorer-human correlation.

    python -m research.annotation.agreement --config configs/annotation.yaml

* 2 annotators: Cohen's kappa (unweighted and quadratic-weighted; the 0-3 scale is ordinal).
* 3+ annotators: Krippendorff's alpha (ordinal), plus mean pairwise weighted kappa.
  (alpha is reported for 2 annotators too, for comparability.)
* Validity of the automatic labels: Spearman between the mean human rating and the
  graded BiasBios relevance label (2 same occupation / 1 same SOC group / 0 other).
* Each scorer: Spearman between its score and the mean human rating over the annotated
  pairs. Raw scores are comparable within a scorer, so no normalisation is needed.
95% CIs: percentile bootstrap over annotated pairs (seeded).
Writes results/annotation_agreement.md and results/annotation/correlations.csv.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

from research.annotation.storage import load_all
from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.metrics.stats import bootstrap_ci


def krippendorff_ordinal(wide: pd.DataFrame) -> float:
    import krippendorff

    data = wide.T.to_numpy(dtype=float)          # rows = annotators, cols = units, NaN = missing
    return float(krippendorff.alpha(reliability_data=data, level_of_measurement="ordinal"))


def kappas(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, b in combinations(wide.columns, 2):
        both = wide[[a, b]].dropna()
        if len(both) < 2:
            continue
        rows.append({"a": a, "b": b, "n": len(both),
                     "kappa": cohen_kappa_score(both[a], both[b]),
                     "kappa_quadratic": cohen_kappa_score(both[a], both[b], weights="quadratic")})
    return pd.DataFrame(rows)


def spearman_ci(x: np.ndarray, y: np.ndarray, n_boot: int, alpha: float, seed: int):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]

    def stat(idx):
        if len(np.unique(x[idx])) < 2 or len(np.unique(y[idx])) < 2:
            return float("nan")
        return float(spearmanr(x[idx], y[idx]).statistic)

    return bootstrap_ci(n_units=len(x), stat_fn=stat, n_boot=n_boot, alpha=alpha, seed=seed), int(len(x))


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/annotation.yaml").parse_args(argv)
    cfg = setup_run(args)
    a = cfg["annotation"]
    nb, al, seed = int(a["bootstrap"]["n"]), float(a["bootstrap"]["alpha"]), int(cfg["seed"])
    wide = load_all(repo_path(a["labels_dir"]))
    if wide.empty:
        print(f"No ratings found in {a['labels_dir']}. Annotate first: streamlit run research/annotation/app.py")
        return
    multi = wide[wide.notna().sum(axis=1) >= 2]
    meta = pd.read_csv(repo_path(a["meta_csv"]), dtype={"pair_id": str}).set_index("pair_id")
    mean_h = wide.mean(axis=1).rename("human_mean")

    lines = ["# Human annotation: agreement and correlations", "",
             f"Annotators: {', '.join(wide.columns)}; pairs rated by anyone: {len(wide)}; "
             f"by 2+ annotators: {len(multi)} (of {len(meta)} sampled).", ""]
    if len(wide.columns) >= 2 and len(multi) >= 2:
        k = kappas(wide)
        alpha_v = krippendorff_ordinal(multi)
        boot = bootstrap_ci(n_units=len(multi), stat_fn=lambda idx: krippendorff_ordinal(multi.iloc[idx]),
                            n_boot=nb, alpha=al, seed=seed)
        lines += ["## Agreement", "",
                  f"- Krippendorff's alpha (ordinal): **{alpha_v:.3f}** [{boot[1]:.3f}, {boot[2]:.3f}]", ""]
        lines += ["| annotator A | annotator B | pairs | Cohen's kappa | quadratic-weighted kappa |", "|---|---|---|---|---|"]
        lines += [f"| {r.a} | {r.b} | {r.n} | {r.kappa:.3f} | {r.kappa_quadratic:.3f} |" for r in k.itertuples()]
        if len(wide.columns) >= 3:
            lines += ["", f"Mean pairwise quadratic-weighted kappa: {k['kappa_quadratic'].mean():.3f}"]
    else:
        lines += ["Agreement needs at least two annotators rating the same pairs.", ""]

    j = meta.join(mean_h, how="inner")
    (rho, lo, hi), n = spearman_ci(j["human_mean"], j["rel_graded"], nb, al, seed)
    lines += ["", "## Validity of the automatic relevance labels", "",
              f"Spearman(mean human rating, graded BiasBios label) = **{rho:.3f}** [{lo:.3f}, {hi:.3f}] (n = {n}).", "",
              "| automatic label | pairs | mean human rating |", "|---|---|---|"]
    for lab, g in j.groupby("rel_graded"):
        lines.append(f"| {lab} | {len(g)} | {g['human_mean'].mean():.2f} |")

    scores = pd.read_parquet(repo_path(a["scores_parquet"]))
    s = scores[(scores["split"] == a["split"]) & (scores["condition"] == "original")]
    s = s.merge(meta.reset_index()[["pair_id", "jd_id", "bio_id"]], on=["jd_id", "bio_id"])
    rows = []
    for scorer, g in s.groupby("scorer", sort=False):
        g = g.set_index("pair_id").join(mean_h, how="inner")
        (rho, lo, hi), n = spearman_ci(g["score"], g["human_mean"], nb, al, seed)
        rows.append({"scorer": scorer, "spearman": rho, "ci_low": lo, "ci_high": hi, "n": n})
    corr = pd.DataFrame(rows).sort_values("spearman", ascending=False)
    lines += ["", "## Scorer vs mean human rating (Spearman)", "",
              "| scorer | rho | 95% CI | pairs |", "|---|---|---|---|"]
    lines += [f"| {r.scorer} | {r.spearman:.3f} | [{r.ci_low:.3f}, {r.ci_high:.3f}] | {r.n} |" for r in corr.itertuples()]

    out_dir = repo_path(cfg["paths"]["results"]) / "annotation"
    out_dir.mkdir(parents=True, exist_ok=True)
    corr.to_csv(out_dir / "correlations.csv", index=False)
    (repo_path(cfg["paths"]["results"]) / "annotation_agreement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_run_metadata(out_dir, cfg, extra={"annotators": list(wide.columns), "n_pairs": len(wide)})
    print("\n".join(lines))


if __name__ == "__main__":
    main()
