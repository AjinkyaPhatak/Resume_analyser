"""Package the paper's final method for the web app (backend/artifacts/entity_li.json).

    python -m research.analysis.export_app [--config configs/main.yaml]

Everything the app needs that is not model weights, all taken from the FINAL runs:
  * the ``entity_li`` scorer spec + its backbone spec (configs/scorers.yaml, unchanged),
  * the entity IDF table, fitted exactly as run.py does (all pool JDs),
  * calibration: quantiles of entity_li scores on DEV pairs (original bios), by graded
    relevance, so the app can say where a score falls (dev only, never test),
  * per-scorer median pool SD on DEV, to express counterfactual gaps in the same
    normalised units as the paper,
  * the near-miss suggestion band chosen on DEV by the Phase 6 rule (nearmiss_grid_dev.csv).
Model weights are not copied: the app loads them from research/models and the HF cache.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import load_config, repo_path
from research.common.provenance import git_info
from research.scorers.registry import build_scorer

OUT = "backend/artifacts/entity_li.json"
COMPARE = ["sbert_minilm", "backend_match"]       # full-text baseline + the old app matcher


def _spec(cfg: dict, name: str) -> dict:
    return next(s for s in cfg["scorers"] if s["name"] == name)


def main(argv=None):
    p = base_parser(__doc__, default_config="configs/main.yaml")
    p.add_argument("--main-dir", default="research/results/main")
    args = p.parse_args(argv)
    cfg = setup_run(args)
    main_dir = repo_path(args.main_dir)
    proc = repo_path(cfg["paths"]["processed_data"])

    # --- IDF, fitted as in run.py (fit_scorer(..., jd_corpus = all pool JDs)) -----------
    spec = _spec(cfg, "entity_li")
    scorer = build_scorer(spec, cfg)
    jds = pd.read_parquet(proc / "jds.parquet")["text"].tolist()
    scorer.fit(jds)
    idf = {k: round(v, 6) for k, v in sorted(scorer.idf.items())}

    # --- calibration on DEV original bios ------------------------------------------------
    s = pd.read_parquet(main_dir / "scores.parquet",
                        filters=[("split", "==", "dev"), ("condition", "==", "original")])
    pools = pd.read_parquet(proc / "pools_dev.parquet")[["jd_id", "bio_id", "rel_graded"]]
    ent = s[s.scorer == "entity_li"].merge(pools, on=["jd_id", "bio_id"], validate="one_to_one")
    qs = np.linspace(0, 1, 101)
    calib = {"split": "dev", "n_pairs": int(len(ent)), "quantile_levels": [round(q, 2) for q in qs]}
    for label, grp in (("all", ent), ("relevant", ent[ent.rel_graded == 2]),
                       ("related", ent[ent.rel_graded == 1]), ("irrelevant", ent[ent.rel_graded == 0])):
        calib[label] = {"n": int(len(grp)), "quantiles": [round(float(x), 6) for x in np.quantile(grp.score, qs)],
                        "mean": round(float(grp.score.mean()), 6)}

    # --- typical pool SD per scorer (DEV) -----------------------------------------------
    pp = pd.read_parquet(main_dir / "per_pool.parquet")
    # pool_sd (SD of the pool's ORIGINAL scores) is stored on the perturbed-condition rows
    pp = pp[(pp.split == "dev") & (pp.condition != "original")].drop_duplicates(["scorer", "jd_id"])
    pool_sd = {k: round(float(v), 6) for k, v in pp.groupby("scorer")["pool_sd"].median().sort_index().items()}
    if any(np.isnan(v) for v in pool_sd.values()):
        raise ValueError(f"missing pool SDs: {pool_sd}")

    # --- near-miss band (Phase 6 rule, DEV) ----------------------------------------------
    nm_cfg = load_config("configs/ablations/nearmiss.yaml")["nearmiss"]
    res = repo_path(cfg["paths"]["results"])
    dev = pd.read_csv(res / "nearmiss_grid_dev.csv")
    test = pd.read_csv(res / "nearmiss_grid_test.csv")
    eligible = dev[dev["n"] >= int(nm_cfg["min_suggestions_dev"])]
    row = eligible.sort_values([nm_cfg["select_on"], "n"], ascending=[False, False]).iloc[0]
    lo, hi = round(float(row.lo), 2), round(float(row.hi), 2)
    trow = test[(test.lo.round(2) == lo) & (test.hi.round(2) == hi)].iloc[0]
    nearmiss = {"band": [lo, hi], "extractor": nm_cfg["extractor"], "backbone": nm_cfg["backbone"],
                "dev_lenient_precision": round(float(row.lenient), 4),
                "test_lenient_precision": round(float(trow.lenient), 4),
                "test_strict_precision": round(float(trow.strict), 4),
                "old_band": nm_cfg["backend_band"]}

    out = {
        "method": {"scorer": spec, "backbones": {b: cfg["backbones"][b] for b in sorted(cfg["backbones"])},
                   "compare": [_spec(cfg, n) for n in COMPARE]},
        "idf": {"n_docs": len(set(jds)), "unseen": round(scorer.idf_unseen, 6), "table": idf},
        "calibration": calib,
        "pool_sd_dev_median": pool_sd,
        "nearmiss": nearmiss,
        "provenance": {"git": git_info(), "main_dir": args.main_dir,
                       "main_run_commit": json.loads((main_dir / "run_meta.json").read_text(encoding="utf-8"))
                       .get("git", {}).get("commit")},
    }
    path = repo_path(OUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, sort_keys=True, allow_nan=False), encoding="utf-8")
    print(f"wrote {path} ({len(idf)} IDF entries, band {lo}-{hi})")


if __name__ == "__main__":
    main()
