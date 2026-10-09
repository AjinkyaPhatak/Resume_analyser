"""Robustness check: results on test pools that no earlier run had touched.

    python -m research.analysis.fresh_pools --config configs/analysis.yaml

The candidate family for the final method was motivated by Phase 6 ablations that were run
on a 200-pool test subset (results/main_subset200 pools). The test pools OUTSIDE that subset
were never used before the final run, so they are a clean held-out check of the design
iteration. Writes results/fresh_pools_check.md.
"""

from __future__ import annotations

import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.metrics.stats import bootstrap_ci


def main(argv=None):
    p = base_parser(__doc__, default_config="configs/analysis.yaml")
    p.add_argument("--seen-dir", default="research/results/main_subset200")
    args = p.parse_args(argv)
    cfg = setup_run(args)
    a = cfg["analysis"]
    full = pd.read_parquet(repo_path(a["main_dir"]) / "per_pool.parquet")
    seen_pp = pd.read_parquet(repo_path(args.seen_dir) / "per_pool.parquet")
    seen = set(seen_pp.loc[seen_pp.split == "test", "jd_id"])
    test = full[full.split == "test"]
    fresh = test[~test.jd_id.isin(seen)]
    seed, nb = int(cfg["seed"]), int(cfg["experiment"]["bootstrap"]["n"])
    h = a["headline"]
    lines = ["# Held-out check: test pools never used before the final run", "",
             f"{fresh.jd_id.nunique()} fresh test pools (of {test.jd_id.nunique()}); the other "
             f"{test.jd_id.nunique() - fresh.jd_id.nunique()} were used by the subset-200 smoke test and the Phase 6 "
             "ablations that motivated the final method's candidate family. Mean over pools [95% cluster-bootstrap CI].", "",
             f"| scorer | {h['x_metric']} (fresh) | {h['y_condition']} |gap| (fresh) | {h['x_metric']} (all test) |",
             "|---|---|---|---|"]
    for s, g in fresh.groupby("scorer", sort=False):
        x = bootstrap_ci(g.loc[g.condition == "original", h["x_metric"]].to_numpy(), n_boot=nb, seed=seed)
        y = bootstrap_ci(g.loc[g.condition == h["y_condition"], h["y_metric"]].to_numpy(), n_boot=nb, seed=seed)
        allx = test[(test.scorer == s) & (test.condition == "original")][h["x_metric"]].mean()
        lines.append(f"| {s} | {x[0]:.3f} [{x[1]:.3f}, {x[2]:.3f}] | {y[0]:.3f} [{y[1]:.3f}, {y[2]:.3f}] | {allx:.3f} |")
    out = repo_path(cfg["paths"]["results"]) / "fresh_pools_check.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
