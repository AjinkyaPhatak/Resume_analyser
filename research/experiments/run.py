"""Phase 5: the main experiment harness.

    python -m research.experiments.run --config configs/main.yaml [--subset N]

1. Loads pools (dev, test), bios, JDs and the Phase 4 counterfactual texts.
2. For every enabled scorer: fits corpus statistics, scores every original (bio, JD) pair
   and every CHANGED counterfactual pair (unchanged counterfactuals reuse the original
   score, so their gap is exactly 0).
3. Computes per-pool metrics, then cluster-bootstrap CIs over pools and paired
   permutation tests (our method vs each baseline, Holm-corrected).

Outputs (results/<experiment.name>[_subsetN]/):
  scores.parquet      long table: scorer, split, condition, jd_id, bio_id, score, nonempty
  per_pool.parquet    per-pool metric values (the bootstrap / test units)
  metrics.csv         tidy: scorer, split, condition, metric, value, ci_low, ci_high, n_units
  tests.csv           ours-vs-baseline paired permutation tests
  run_meta.json       config, git hash, environment, timings
and results/<name>[_subsetN]_summary.md with the headline tables.
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng
from research.metrics.fairness import best_f1_threshold, pool_counterfactual, pool_exposure, pool_zscores
from research.metrics.ranking import pool_ranking_metrics
from research.metrics.stats import bootstrap_ci, holm, paired_permutation_test
from research.scorers.entity import EntityLateInteractionScorer
from research.scorers.registry import build_scorers, fit_scorer

RANKING_METRICS = ["ndcg@10", "ndcg@10_binary", "mrr", "p@5", "p@10"]


# ----------------------------------------------------------------------------------- data

def load_inputs(cfg: dict) -> dict:
    proc = repo_path(cfg["paths"]["processed_data"])
    out = {"jds": pd.read_parquet(proc / "jds.parquet").set_index("jd_id")["text"]}
    for split in ("dev", "test"):
        out[f"pools_{split}"] = pd.read_parquet(proc / f"pools_{split}.parquet")
        out[f"bios_{split}"] = pd.read_parquet(proc / f"bios_{split}.parquet").set_index("bio_id")["text"]
        out[f"pert_{split}"] = pd.read_parquet(proc / f"perturbations_{split}.parquet")
    train = pd.read_parquet(proc / "bios_train.parquet", columns=["text"])
    n = min(int(cfg["fit"]["lexical_train_bios"]), len(train))
    idx = np.sort(make_rng(int(cfg["seed"])).permutation(len(train))[:n])
    out["lexical_corpus"] = train["text"].iloc[idx].tolist() + out["jds"].tolist()
    return out


def select_pools(pools: pd.DataFrame, n: int | None, seed: int) -> pd.DataFrame:
    if not n:
        return pools
    ids = sorted(pools["jd_id"].unique())
    keep = {ids[i] for i in make_rng(seed).permutation(len(ids))[:n]}
    return pools[pools["jd_id"].isin(keep)].reset_index(drop=True)


def orientation_sign(condition: str, gender: str, changes_json: str, orient: dict) -> int:
    kind = orient.get(condition, orient.get("default", "gender"))
    if kind == "gender":
        return 1 if gender == "M" else -1          # perturbed version of a male bio is the female-coded one
    if kind == "communal":
        ch = json.loads(changes_json)
        a2c = sum(c["kind"] == "agentic->communal" for c in ch)
        c2a = sum(c["kind"] == "communal->agentic" for c in ch)
        return 1 if a2c >= c2a else -1
    if kind == "target":
        return 1
    raise ValueError(f"unknown orientation {kind!r}")


def build_pair_table(pools: pd.DataFrame, pert: pd.DataFrame, conditions: list[str], orient: dict) -> pd.DataFrame:
    """One row per (pool, bio, condition) incl. 'original', with text keys and orientation."""
    base = pools[["jd_id", "bio_id", "bio_gender"]].copy()
    rows = [base.assign(condition="original", changed=False, sign=0, pert_text=None)]
    p = pert[pert["condition"].isin(conditions)][["bio_id", "condition", "text", "changed", "changes"]]
    m = base.merge(p, on="bio_id", how="left")
    if m["condition"].isna().any():
        missing = m.loc[m["condition"].isna(), "bio_id"].nunique()
        raise ValueError(f"{missing} pooled bios have no counterfactuals; rerun make_perturbations")
    m["sign"] = [orientation_sign(c, g, ch, orient) for c, g, ch in zip(m["condition"], m["bio_gender"], m["changes"])]
    m = m.rename(columns={"text": "pert_text"}).drop(columns=["changes"])
    rows.append(m)
    return pd.concat(rows, ignore_index=True)


# -------------------------------------------------------------------------------- scoring

def score_split(scorer, table: pd.DataFrame, bios: pd.Series, jds: pd.Series, chunk: int) -> pd.DataFrame:
    """Score originals + changed counterfactuals; unchanged counterfactuals copy the original."""
    need = table[(table["condition"] == "original") | table["changed"]].copy()
    need["resume"] = np.where(need["condition"] == "original", need["bio_id"].map(bios), need["pert_text"])
    need["jd"] = need["jd_id"].map(jds)
    pairs = list(zip(need["resume"], need["jd"]))
    scores = []
    for i in range(0, len(pairs), chunk):
        scores += scorer.score_batch(pairs[i : i + chunk])
    need["score"] = np.asarray(scores, float)
    if isinstance(scorer, EntityLateInteractionScorer):
        need["nonempty"] = scorer.nonempty_batch(pairs)
    else:
        need["nonempty"] = True
    out = table.merge(need[["jd_id", "bio_id", "condition", "score", "nonempty"]],
                      on=["jd_id", "bio_id", "condition"], how="left")
    orig = out[out["condition"] == "original"].set_index(["jd_id", "bio_id"])
    fill = out["score"].isna()
    keys = list(zip(out.loc[fill, "jd_id"], out.loc[fill, "bio_id"]))
    out.loc[fill, "score"] = orig["score"].reindex(keys).to_numpy()
    out.loc[fill, "nonempty"] = orig["nonempty"].reindex(keys).to_numpy()
    return out


# -------------------------------------------------------------------------------- metrics

def per_pool_metrics(scored: pd.DataFrame, pools: pd.DataFrame, conditions: list[str], exposure_k: int) -> pd.DataFrame:
    """scored: one split, one scorer (output of score_split)."""
    meta = pools.set_index(["jd_id", "bio_id"])
    orig = scored[scored["condition"] == "original"].set_index(["jd_id", "bio_id"])
    rows = []
    for jd, og in orig.groupby(level=0, sort=True):
        m = meta.loc[og.index]
        s = og["score"].to_numpy()
        r = {"jd_id": jd, "condition": "original", "jd_occupation": m["jd_occupation"].iloc[0]}
        r.update(pool_ranking_metrics(s, m["rel_binary"].to_numpy(), m["rel_graded"].to_numpy()))
        r.update(pool_exposure(s, m["bio_gender"].to_numpy(), exposure_k))
        r["frac_nonempty"] = float(og["nonempty"].astype(bool).mean())
        rows.append(r)
    pert = scored[scored["condition"] != "original"]
    for (cond, jd), pg in pert.groupby(["condition", "jd_id"], sort=True):
        pg = pg.set_index("bio_id").loc[orig.loc[jd].index]            # align with original order
        o = orig.loc[jd]
        changed = pg["changed"].to_numpy(bool)
        r = {"jd_id": jd, "condition": cond}
        r.update(pool_counterfactual(o["score"].to_numpy(), pg["score"].to_numpy(), pg["sign"].to_numpy(), changed))
        both = changed & o["nonempty"].to_numpy(bool) & pg["nonempty"].to_numpy(bool)
        sub = pool_counterfactual(o["score"].to_numpy(), pg["score"].to_numpy(), pg["sign"].to_numpy(), both)
        r.update({k.replace("_changed", "_changed_nonempty"): v for k, v in sub.items() if k.endswith("_changed")})
        r["n_changed_nonempty"] = int(both.sum())
        rows.append(r)
    return pd.DataFrame(rows)


def tpr_gap_with_ci(dev: pd.DataFrame, test: pd.DataFrame, pools_dev: pd.DataFrame, pools_test: pd.DataFrame,
                    n_boot: int, alpha: float, seed: int) -> dict:
    """Threshold from DEV (best F1 on per-pool z-scores), TPR gap on TEST, CI over test pools."""
    def prep(scored, pools):
        o = scored[scored["condition"] == "original"].merge(pools, on=["jd_id", "bio_id", "bio_gender"])
        o["z"] = pool_zscores(o)
        return o
    d, t = prep(dev, pools_dev), prep(test, pools_test)
    thr = best_f1_threshold(d["z"].to_numpy(), d["rel_binary"].to_numpy())
    rel = t[t["rel_binary"] == 1].copy()
    rel["hit"] = (rel["z"] >= thr).astype(float)
    # per-pool counts -> fast resampling
    g = rel.groupby(["jd_id", "jd_occupation", "bio_gender"])["hit"].agg(["sum", "count"]).unstack("bio_gender", fill_value=0)
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    g = g.reset_index()
    occ_codes, occ_names = pd.factorize(g["jd_occupation"])
    arr = g[["sum_F", "count_F", "sum_M", "count_M"]].to_numpy(float)

    def stat(idx, kind):
        c = np.zeros((len(occ_names), 4))
        np.add.at(c, occ_codes[idx], arr[idx])
        ok = (c[:, 1] > 0) & (c[:, 3] > 0)
        gaps = c[ok, 0] / c[ok, 1] - c[ok, 2] / c[ok, 3]
        if not len(gaps):
            return float("nan")
        return float(np.sqrt((gaps ** 2).mean())) if kind == "rms" else float(gaps.mean())

    out = {"threshold": thr}
    out["mean"] = bootstrap_ci(n_units=len(g), stat_fn=lambda idx: stat(idx, "mean"), n_boot=n_boot,
                               alpha=alpha, seed=seed)
    # RMS: point estimate only. Pool resampling adds noise to every per-occupation TPR, which
    # inflates an RMS so strongly that almost all replicates exceed the estimate; neither the
    # percentile nor the basic bootstrap interval is then valid (checked on the full run).
    out["rms"] = (stat(np.arange(len(g)), "rms"), float("nan"), float("nan"))
    return out


def summarise(per_pool: pd.DataFrame, n_boot: int, alpha: float, seed: int) -> pd.DataFrame:
    rows = []
    skip = {"scorer", "split", "condition", "jd_id", "jd_occupation", "n_bios", "pool_sd"}
    for (scorer, split, cond), g in per_pool.groupby(["scorer", "split", "condition"], sort=False):
        for col in g.columns:
            if col in skip or not np.issubdtype(g[col].dtype, np.number) or g[col].isna().all():
                continue
            vals = g[col].to_numpy(float)
            if col.startswith("n_"):
                rows.append({"scorer": scorer, "split": split, "condition": cond, "metric": col,
                             "value": float(np.nansum(vals)), "ci_low": np.nan, "ci_high": np.nan,
                             "n_units": int((~np.isnan(vals)).sum())})
                continue
            v, lo, hi = bootstrap_ci(vals, n_boot=n_boot, alpha=alpha, seed=seed)
            rows.append({"scorer": scorer, "split": split, "condition": cond, "metric": col, "value": v,
                         "ci_low": lo, "ci_high": hi, "n_units": int((~np.isnan(vals)).sum())})
    return pd.DataFrame(rows)


def significance(per_pool: pd.DataFrame, ours: str, conditions: list[str], fair_metrics: list[str],
                 n_perm: int, seed: int) -> pd.DataFrame:
    test = per_pool[per_pool["split"] == "test"]
    rows = []
    families = [("original", m) for m in ("ndcg@10",)] + [(c, m) for c in conditions for m in fair_metrics]
    for cond, metric in families:
        sub = test[test["condition"] == cond].pivot_table(index="jd_id", columns="scorer", values=metric)
        if ours not in sub:
            continue
        fam = []
        for other in sub.columns:
            if other == ours:
                continue
            r = paired_permutation_test(sub[ours].to_numpy(), sub[other].to_numpy(), n_perm=n_perm, seed=seed)
            fam.append({"condition": cond, "metric": metric, "ours": ours, "baseline": other, **r})
        for r, p_adj in zip(fam, holm([r["p_value"] for r in fam])):
            r["p_holm"] = p_adj
        rows += fam
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------- reporting

def write_summary(path, metrics: pd.DataFrame, tests: pd.DataFrame, tpr: dict, cfg: dict, timings: dict,
                  conditions: list[str], split: str = "test") -> None:
    def fmt(r):
        return "–" if pd.isna(r["value"]) else f"{r['value']:.3f} [{r['ci_low']:.3f}, {r['ci_high']:.3f}]"

    def get(scorer, split, cond, metric):
        m = metrics[(metrics.scorer == scorer) & (metrics.split == split) & (metrics.condition == cond)
                    & (metrics.metric == metric)]
        return fmt(m.iloc[0]) if len(m) else "–"

    scorers = list(dict.fromkeys(metrics["scorer"]))
    sub = cfg.get("subset")
    lines = [f"# {'PRELIMINARY SMOKE TEST (--subset ' + str(sub) + ' pools per split)' if sub else 'Main results'}", "",
             f"{split.capitalize()} pools unless noted. Values: mean over JD pools [95% cluster-bootstrap CI over pools, "
             f"{cfg['experiment']['bootstrap']['n']} resamples]. Gaps: |score change| / SD of the pool's original "
             "scores, over CHANGED bios. Signed gaps: + = favours the female-coded (communal / target) version.", "",
             f"## Ranking accuracy ({split})", "",
             "| Scorer | nDCG@10 | MRR | P@5 | P@10 | pairs with entities |", "|---|---|---|---|---|---|"]
    for s in scorers:
        lines.append(f"| {s} | {get(s, split, 'original', 'ndcg@10')} | {get(s, split, 'original', 'mrr')} | "
                     f"{get(s, split, 'original', 'p@5')} | {get(s, split, 'original', 'p@10')} | "
                     f"{get(s, split, 'original', 'frac_nonempty')} |")
    for metric, title in (("abs_gap_norm_changed", "Counterfactual |gap| (normalised, changed bios)"),
                          ("signed_gap_norm_changed", "Signed gap (normalised, changed bios; + favours female/communal/target)"),
                          ("abs_rank_shift_changed", "Mean |rank shift| in the pool (changed bios)")):
        lines += ["", f"## {title}", "", "| Scorer | " + " | ".join(conditions) + " |", "|---|" + "---|" * len(conditions)]
        for s in scorers:
            lines.append(f"| {s} | " + " | ".join(get(s, split, c, metric) for c in conditions) + " |")
    cov = metrics[(metrics.split == split) & (metrics.condition == "original") & (metrics.metric == "frac_nonempty")]
    ent = [s for s in scorers if (cov.loc[cov.scorer == s, "value"] < 1).any()]   # scorers with empty-entity pairs
    if ent:
        lines += ["", "## Entity scorers: |gap| restricted to pairs where both sides have entities", "",
                  "| Scorer | " + " | ".join(conditions) + " |", "|---|" + "---|" * len(conditions)]
        for s in ent:
            lines.append(f"| {s} | " + " | ".join(get(s, split, c, "abs_gap_norm_changed_nonempty") for c in conditions) + " |")
    lines += ["", "## TPR gender gap (threshold chosen on dev; TPR_F - TPR_M over JD occupations)", "",
              "| Scorer | threshold (z) | mean gap | RMS gap |", "|---|---|---|---|"]
    for s, t in tpr.items():
        lines.append(f"| {s} | {t['threshold']:.2f} | {t['mean'][0]:.3f} [{t['mean'][1]:.3f}, {t['mean'][2]:.3f}] | "
                     f"{t['rms'][0]:.3f} (no CI: bootstrap invalid for RMS here) |")
    lines += ["", "## Top-10 exposure (female share - 0.5; pools are 50/50)", "",
              "| Scorer | top-10 share | discounted exposure |", "|---|---|---|"]
    for s in scorers:
        lines.append(f"| {s} | {get(s, split, 'original', 'topk_female_share_minus_half')} | "
                     f"{get(s, split, 'original', 'exposure_female_share_minus_half')} |")
    if len(tests):
        lines += ["", f"## Paired permutation tests: {cfg['experiment']['our_method']} vs baselines "
                  f"({cfg['experiment']['permutation']['n']} sign flips, Holm within each row family)", "",
                  "| condition | metric | baseline | mean diff (ours - baseline) | p | p (Holm) | pools |", "|---|---|---|---|---|---|---|"]
        for r in tests.itertuples(index=False):
            lines.append(f"| {r.condition} | {r.metric} | {r.baseline} | {r.mean_diff:.4f} | {r.p_value:.4f} | "
                         f"{r.p_holm:.4f} | {r.n_units} |")
    lines += ["", "Scoring wall-clock (s): " + ", ".join(f"{k} {v:.0f}" for k, v in timings.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------- main

def main(argv=None):
    args = base_parser(__doc__, default_config="configs/main.yaml").parse_args(argv)
    cfg = setup_run(args)
    ecfg = cfg["experiment"]
    conditions = ecfg["conditions"]
    seed = int(cfg["seed"])
    name = ecfg["name"] + (f"_subset{cfg['subset']}" if cfg.get("subset") else "")
    out_dir = repo_path(cfg["paths"]["results"]) / name
    out_dir.mkdir(parents=True, exist_ok=True)

    splits = list(ecfg.get("splits", ["dev", "test"]))    # ["dev"] for dev-only model selection
    report_split = "test" if "test" in splits else "dev"
    data = load_inputs(cfg)
    pools = {s: select_pools(data[f"pools_{s}"], cfg.get("subset"), seed) for s in splits}
    tables = {s: build_pair_table(pools[s], data[f"pert_{s}"], conditions, ecfg["orientation"]) for s in splits}
    for s in splits:
        print(f"[{s}] {pools[s]['jd_id'].nunique()} pools, {len(tables[s])} (pair, condition) rows, "
              f"{int((tables[s]['condition'] == 'original').sum() + tables[s]['changed'].sum())} to score", flush=True)

    # reuse_scores: recompute every metric from a previous run's scores.parquet (no re-scoring)
    reuse = None
    if ecfg.get("reuse_scores"):
        reuse = pd.read_parquet(out_dir / "scores.parquet")
        print(f"[reuse] metrics recomputed from {out_dir / 'scores.parquet'}", flush=True)
        names = [s["name"] for s in cfg["scorers"] if s.get("enabled", True)]
        scorer_objs = [type("Reused", (), {"name": n})() for n in names]
    else:
        scorer_objs = build_scorers(cfg)
    all_scores, per_pool, timings, tpr = [], [], {}, {}
    for scorer in scorer_objs:
        t0 = time.perf_counter()
        if reuse is None:
            fit_scorer(scorer, data["lexical_corpus"], data["jds"].tolist())
        scored = {}
        for s in splits:
            if reuse is not None:
                scored[s] = (reuse[(reuse.scorer == scorer.name) & (reuse.split == s)]
                             .drop(columns=["scorer", "split"]).assign(pert_text=None).reset_index(drop=True))
                if scored[s].empty:
                    raise ValueError(f"no saved scores for {scorer.name}/{s} in {out_dir}")
            else:
                scored[s] = score_split(scorer, tables[s], data[f"bios_{s}"], data["jds"], int(ecfg["score_chunk"]))
            pp = per_pool_metrics(scored[s], pools[s], conditions, int(ecfg["exposure_k"]))
            per_pool.append(pp.assign(scorer=scorer.name, split=s))
            all_scores.append(scored[s].drop(columns=["pert_text"]).assign(scorer=scorer.name, split=s))
        if {"dev", "test"} <= set(splits):
            tpr[scorer.name] = tpr_gap_with_ci(scored["dev"], scored["test"], pools["dev"], pools["test"],
                                               int(ecfg["bootstrap"]["n"]), float(ecfg["bootstrap"]["alpha"]), seed)
        timings[scorer.name] = time.perf_counter() - t0
        nan = int(scored[report_split]["score"].isna().sum())
        print(f"[done] {scorer.name}: {timings[scorer.name]:.0f}s, NaN scores in {report_split}: {nan}", flush=True)

    per_pool = pd.concat(per_pool, ignore_index=True)
    metrics = summarise(per_pool, int(ecfg["bootstrap"]["n"]), float(ecfg["bootstrap"]["alpha"]), seed)
    for s, t in tpr.items():
        for kind in ("mean", "rms"):
            v, lo, hi = t[kind]
            metrics.loc[len(metrics)] = {"scorer": s, "split": "test", "condition": "original",
                                         "metric": f"tpr_gap_{kind}", "value": v, "ci_low": lo, "ci_high": hi,
                                         "n_units": np.nan}
    tests = significance(per_pool, ecfg["our_method"], conditions, ecfg["test_metrics"],
                         int(ecfg["permutation"]["n"]), seed) if "test" in splits else pd.DataFrame()

    pd.concat(all_scores, ignore_index=True).to_parquet(out_dir / "scores.parquet", index=False)
    per_pool.to_parquet(out_dir / "per_pool.parquet", index=False)
    metrics.to_csv(out_dir / "metrics.csv", index=False)
    tests.to_csv(out_dir / "tests.csv", index=False)
    write_run_metadata(out_dir, cfg, extra={"timings_s": timings, "tpr_thresholds": {k: v["threshold"] for k, v in tpr.items()},
                                            "n_pools": {s: int(pools[s]["jd_id"].nunique()) for s in pools}})
    summary = repo_path(cfg["paths"]["results"]) / f"{name}_summary.md"
    write_summary(summary, metrics, tests, tpr, cfg, timings, conditions, split=report_split)
    print(summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
