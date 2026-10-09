"""Draw the stratified annotation sample.

    python -m research.annotation.sample --config configs/annotation.yaml

Strata = consensus-score bin x JD occupation x bio gender. The consensus score of a
(bio, JD) pair is the mean, over ``strata_scorers``, of the pair's percentile rank within
its pool, so the sample covers pairs every model likes, dislikes, and disagrees on.

Allocation: the budget is split EQUALLY across score bins (bins are cut at quantiles of
the consensus score, default 50% / 90%), which over-samples high-scoring pairs: pools are
90% irrelevant, so proportional sampling gave ~78% obvious non-matches. Within a bin:
one pair per non-empty occupation x gender stratum first, then proportionally to size
(largest remainder). Uniform seeded draws within strata. Agreement and correlations are
therefore computed on this deliberately score-balanced sample, not population-weighted.

Writes the annotator-facing CSV (pair_id, JD title/text, bio text only) and a separate
metadata CSV with the strata, relevance labels and consensus score, which the app never
reads.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng


def consensus_scores(scores: pd.DataFrame, scorers: list[str], split: str) -> pd.DataFrame:
    s = scores[(scores["split"] == split) & (scores["condition"] == "original") & scores["scorer"].isin(scorers)]
    missing = set(scorers) - set(s["scorer"])
    if missing:
        raise ValueError(f"scores file lacks scorers {sorted(missing)}")
    s = s.assign(pct=s.groupby(["scorer", "jd_id"])["score"].rank(pct=True, method="average"))
    return s.groupby(["jd_id", "bio_id"], as_index=False)["pct"].mean().rename(columns={"pct": "consensus"})


def allocate(sizes: pd.Series, n: int) -> pd.Series:
    """Per-stratum sample sizes: >= 1 per stratum (budget permitting), rest proportional."""
    sizes = sizes[sizes > 0].sort_values(ascending=False)
    if n <= 0 or sizes.empty:
        return pd.Series(0, index=sizes.index)
    alloc = pd.Series(0, index=sizes.index)
    first = sizes.index[: min(n, len(sizes))]
    alloc[first] = 1
    rest = n - int(alloc.sum())
    if rest > 0:
        cap = sizes - alloc
        quota = cap / cap.sum() * rest
        extra = np.floor(quota).astype(int).clip(upper=cap)
        left = rest - int(extra.sum())
        order = (quota - np.floor(quota)).sort_values(ascending=False).index
        for k in order:
            if left == 0:
                break
            if extra[k] < cap[k]:
                extra[k] += 1
                left -= 1
        alloc += extra
    return alloc


def stratified_sample(frame: pd.DataFrame, strata_cols: list[str], n: int, rng) -> pd.DataFrame:
    sizes = frame.groupby(strata_cols).size()
    alloc = allocate(sizes, n)
    parts = []
    for key, k in alloc.items():
        if k == 0:
            continue
        key = key if isinstance(key, tuple) else (key,)
        g = frame
        for col, val in zip(strata_cols, key):
            g = g[g[col] == val]
        parts.append(g.iloc[np.sort(rng.choice(len(g), size=int(k), replace=False))])
    return pd.concat(parts, ignore_index=True)


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/annotation.yaml").parse_args(argv)
    cfg = setup_run(args)
    a = cfg["annotation"]
    proc = repo_path(cfg["paths"]["processed_data"])
    rng = make_rng(int(cfg["seed"]))
    split = a["split"]

    pools = pd.read_parquet(proc / f"pools_{split}.parquet")
    cons = consensus_scores(pd.read_parquet(repo_path(a["scores_parquet"])), a["strata_scorers"], split)
    frame = pools.merge(cons, on=["jd_id", "bio_id"], how="inner")
    if frame.empty:
        raise ValueError("no pooled pairs have scores; check annotation.scores_parquet")
    edges = frame["consensus"].quantile(a["score_bin_quantiles"]).to_numpy().copy()
    edges[0], edges[-1] = -np.inf, np.inf
    frame["score_bin"] = pd.cut(frame["consensus"], edges, labels=False)
    n_bins = int(frame["score_bin"].nunique())
    per_bin = allocate(pd.Series({b: 10**9 for b in range(n_bins)}), int(a["n_pairs"]))   # equal split
    sample = pd.concat([stratified_sample(frame[frame["score_bin"] == b], ["jd_occupation", "bio_gender"], int(k), rng)
                        for b, k in per_bin.sort_index().items()], ignore_index=True)
    sample = sample.iloc[rng.permutation(len(sample))].reset_index(drop=True)
    sample["pair_id"] = [f"p{i:03d}" for i in range(len(sample))]

    jds = pd.read_parquet(proc / "jds.parquet").set_index("jd_id")
    bios = pd.read_parquet(proc / f"bios_{split}.parquet").set_index("bio_id")["text"]
    visible = pd.DataFrame({"pair_id": sample["pair_id"], "jd_title": sample["jd_id"].map(jds["title"]),
                            "jd_text": sample["jd_id"].map(jds["text"]), "bio_text": sample["bio_id"].map(bios)})
    meta = sample[["pair_id", "jd_id", "bio_id", "jd_occupation", "bio_occupation", "bio_gender",
                   "rel_binary", "rel_graded", "consensus", "score_bin"]]
    visible.to_csv(repo_path(a["sample_csv"]), index=False)
    meta.to_csv(repo_path(a["meta_csv"]), index=False)
    write_run_metadata(repo_path(cfg["paths"]["results"]) / "annotation_sample", cfg,
                       extra={"n": len(sample), "strata": int(sample.groupby(["jd_occupation", "bio_gender", "score_bin"]).ngroups)})
    print(f"wrote {len(sample)} pairs -> {a['sample_csv']} (+ hidden metadata {a['meta_csv']})")
    print(meta.groupby(["bio_gender", "score_bin"]).size().unstack().to_string())
    print(meta["jd_occupation"].value_counts().to_string())
    print("relevance:", meta["rel_graded"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
