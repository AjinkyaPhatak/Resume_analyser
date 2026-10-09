"""Phase 3 smoke test: run every enabled scorer on a few DEV pools (never test).

    python -m research.experiments.scorer_smoke --config configs/scorers.yaml [--subset N]

--subset N = number of dev pools (default 10). Reports, per scorer: wall-clock time,
pairs/s, empty-entity count, and a per-pool AUC (P[relevant bio outscores irrelevant
bio], averaged over pools). It's a sanity check that scorers run end to end and are
better than chance. Not a result: the Phase 5 harness computes the real metrics.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng
from research.scorers.registry import build_scorers, fit_scorer


def pool_auc(scores: np.ndarray, rel: np.ndarray) -> float:
    pos, neg = scores[rel == 1], scores[rel == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    diff = pos[:, None] - neg[None, :]
    return float((diff > 0).mean() + 0.5 * (diff == 0).mean())


def load_fit_corpora(cfg, proc):
    train = pd.read_parquet(proc / "bios_train.parquet", columns=["text"])
    n = min(int(cfg["fit"]["lexical_train_bios"]), len(train))
    idx = np.sort(make_rng(int(cfg["seed"])).permutation(len(train))[:n])
    jds = pd.read_parquet(proc / "jds.parquet")
    return train["text"].iloc[idx].tolist() + jds["text"].tolist(), jds


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/scorers.yaml").parse_args(argv)
    cfg = setup_run(args)
    proc = repo_path(cfg["paths"]["processed_data"])
    n_pools = cfg.get("subset") or 10
    pools = pd.read_parquet(proc / "pools_dev.parquet")
    bios = pd.read_parquet(proc / "bios_dev.parquet", columns=["bio_id", "text"]).set_index("bio_id")["text"]
    lex_corpus, jds = load_fit_corpora(cfg, proc)
    jd_text = jds.set_index("jd_id")["text"]
    keep = sorted(pools["jd_id"].unique())
    keep = [keep[i] for i in sorted(make_rng(int(cfg["seed"])).permutation(len(keep))[:n_pools])]
    pools = pools[pools["jd_id"].isin(keep)].reset_index(drop=True)
    pairs = [(bios[b], jd_text[j]) for b, j in zip(pools["bio_id"], pools["jd_id"])]
    print(f"{len(keep)} dev pools, {len(pairs)} pairs")

    rows = []
    for scorer in build_scorers(cfg):
        t0 = time.perf_counter()
        fit_scorer(scorer, lex_corpus, jd_text.tolist())
        t1 = time.perf_counter()
        scores = np.array(scorer.score_batch(pairs), dtype=float)
        t2 = time.perf_counter()
        aucs = [pool_auc(scores[g.index], g["rel_binary"].to_numpy()) for _, g in pools.groupby("jd_id")]
        rows.append({"scorer": scorer.name, "fit_s": round(t1 - t0, 1), "score_s": round(t2 - t1, 1),
                     "pairs_per_s": round(len(pairs) / max(t2 - t1, 1e-9), 1),
                     "n_nan": int(np.isnan(scores).sum()), "n_empty": getattr(scorer, "n_empty", None),
                     "mean_pool_auc": round(float(np.nanmean(aucs)), 3),
                     "score_mean_rel": round(float(np.nanmean(scores[pools["rel_binary"] == 1])), 4),
                     "score_mean_irrel": round(float(np.nanmean(scores[pools["rel_binary"] == 0])), 4)})
        print(rows[-1], flush=True)

    out = pd.DataFrame(rows)
    res = repo_path(cfg["paths"]["results"])
    lines = ["# Scorer smoke test (DEV pools, PRELIMINARY sanity check, not a result)", "",
             f"{len(keep)} dev pools x 100 bios = {len(pairs)} pairs; seed {cfg['seed']}. "
             "Times include first-time extraction/embedding (later runs hit the caches). "
             "AUC = P(relevant bio outscores irrelevant bio) within a pool, averaged over pools.", "",
             "| " + " | ".join(out.columns) + " |", "|" + "---|" * len(out.columns)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in out.itertuples(index=False)]
    (res / "scorer_smoke.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_run_metadata(res / "scorer_smoke", cfg, extra={"jd_ids": keep, "n_pairs": len(pairs)})
    print("\n".join(lines))


if __name__ == "__main__":
    main()
