"""Export the paper's results for the website's research page.

    python -m research.analysis.export_web [--config configs/analysis.yaml]

Writes frontend/public/research/data.json and copies the final figures (PDF + PNG) to
frontend/public/research/figures/. Every number comes from the FINAL full runs
(results/main, results/ablation_*, results/selection_dev, the near-miss grids, the
extraction metrics and the tagger training histories); files from --subset runs and
``*_preliminary`` figures are never exported. Rerun after any result changes.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import load_config, repo_path
from research.metrics.stats import bootstrap_ci

OUT_DIR = "frontend/public/research"
CONDITIONS = ["pronoun_swap", "name_swap_us", "name_swap_in", "name_in_same_gender",
              "affiliation_swap", "agentic_communal", "gender_full"]
CONDITION_LABELS = {
    "pronoun_swap": "Pronoun swap", "name_swap_us": "Name swap (US)", "name_swap_in": "Name swap (Indian)",
    "name_in_same_gender": "Indian name, same gender", "affiliation_swap": "Affiliation swap",
    "agentic_communal": "Agentic → communal", "gender_full": "Full gender flip",
}
SCORERS = {   # id -> (label, family, one-line description)
    "bm25": ("BM25", "lexical", "Okapi BM25 over words (stop-words incl. pronouns removed)"),
    "tfidf": ("TF-IDF", "lexical", "TF-IDF cosine over words (same stop-words)"),
    "sbert_minilm": ("MiniLM", "full-text", "all-MiniLM-L6-v2 embedding of the whole text"),
    "sbert_mpnet": ("MPNet", "full-text", "all-mpnet-base-v2 embedding of the whole text"),
    "jobbert_v2": ("JobBERT-v2", "full-text", "TechWolf/JobBERT-v2 embedding of the whole text (64-token windows)"),
    "cross_encoder": ("Cross-encoder", "full-text", "ms-marco-MiniLM-L6-v2 reading resume and JD together"),
    "backend_match": ("Old app matcher", "legacy", "This app's original matcher: noun chunks, MiniLM, share of JD entities ≥ 0.55"),
    "entity_li": ("Entity LI (ours)", "entity", "Skill entities (JobBERT tagger + ESCO + noun chunks), JobBERT-v2, IDF-weighted MaxSim"),
}
ABLATIONS = {
    "extractor": ("Which skill extractor?", "MiniLM, MaxSim-mean; only the extractor changes",
                  {"ex_noun_chunk": "Noun chunks (old app)", "ex_esco": "ESCO ruler", "ex_jobbert_ft": "Fine-tuned JobBERT",
                   "ex_union": "JobBERT + ESCO"}),
    "entity_types": ("Which entity types?", "JobBERT + ESCO extractor, MiniLM, MaxSim-mean",
                     {"ent_skills_only": "Skills only", "ent_plus_noun_chunks": "+ filtered noun chunks",
                      "ent_plus_noun_chunks_verbs": "+ noun chunks + verb phrases"}),
    "backbone": ("Which entity encoder?", "JobBERT + ESCO extractor, MaxSim-mean",
                 {"bb_minilm": "MiniLM", "bb_mpnet": "MPNet", "bb_jobbert_v2": "JobBERT-v2"}),
    "aggregation": ("How to aggregate?", "JobBERT + ESCO extractor, MiniLM",
                    {"agg_maxsim_mean": "MaxSim mean", "agg_hungarian": "Hungarian (1-to-1)",
                     "agg_idf_weighted": "IDF-weighted MaxSim"}),
}
FIGURES = ["headline_accuracy_vs_gap", "perturbation_gaps", "nearmiss_curves", "nearmiss_heatmap_dev"]


def _ci(df: pd.DataFrame, scorer: str, split: str, condition: str, metric: str):
    r = df[(df.scorer == scorer) & (df.split == split) & (df.condition == condition) & (df.metric == metric)]
    if r.empty:
        return None
    r = r.iloc[0]
    vals = [r.value, r.ci_low, r.ci_high]
    return [None if pd.isna(v) else round(float(v), 6) for v in vals]   # display rounds once


def main_results(main_dir) -> dict:
    m = pd.read_csv(main_dir / "metrics.csv")
    out: dict = {"ranking": {}, "abs_gap": {}, "signed_gap": {}, "rank_shift": {}, "abs_gap_nonempty": {},
                 "tpr_gap_mean": {}, "tpr_gap_rms": {}, "exposure": {}, "frac_nonempty": {}, "dev_ranking": {}}
    for s in SCORERS:
        out["ranking"][s] = {k: _ci(m, s, "test", "original", k) for k in ("ndcg@10", "mrr", "p@5", "p@10")}
        out["dev_ranking"][s] = {"ndcg@10": _ci(m, s, "dev", "original", "ndcg@10")}
        out["frac_nonempty"][s] = _ci(m, s, "test", "original", "frac_nonempty")
        out["tpr_gap_mean"][s] = _ci(m, s, "test", "original", "tpr_gap_mean")
        rms = _ci(m, s, "test", "original", "tpr_gap_rms")
        out["tpr_gap_rms"][s] = rms[0] if rms else None          # point estimate only (see CLAUDE.md)
        out["exposure"][s] = _ci(m, s, "test", "original", "topk_female_share_minus_half")
        for key, metric in (("abs_gap", "abs_gap_norm_changed"), ("signed_gap", "signed_gap_norm_changed"),
                            ("rank_shift", "abs_rank_shift_changed"),
                            ("abs_gap_nonempty", "abs_gap_norm_changed_nonempty")):
            out[key][s] = {c: _ci(m, s, "test", c, metric) for c in CONDITIONS}
    t = pd.read_csv(main_dir / "tests.csv")
    keep = t.metric.isin(["ndcg@10", "abs_gap_norm_changed"])
    out["tests"] = [{"condition": r.condition, "metric": r.metric, "baseline": r.baseline,
                     "mean_diff": round(float(r.mean_diff), 4), "p_holm": float(r.p_holm), "n": int(r.n_units)}
                    for r in t[keep].itertuples()]
    return out


def fresh_pools(main_dir, seen_dir, seed: int, n_boot: int) -> dict:
    full = pd.read_parquet(main_dir / "per_pool.parquet")
    seen_pp = pd.read_parquet(seen_dir / "per_pool.parquet")
    seen = set(seen_pp.loc[seen_pp.split == "test", "jd_id"])
    test = full[full.split == "test"]
    fresh = test[~test.jd_id.isin(seen)]
    rows = {}
    for s, g in fresh.groupby("scorer", sort=False):
        x = bootstrap_ci(g.loc[g.condition == "original", "ndcg@10"].to_numpy(), n_boot=n_boot, seed=seed)
        y = bootstrap_ci(g.loc[g.condition == "gender_full", "abs_gap_norm_changed"].to_numpy(), n_boot=n_boot, seed=seed)
        rows[s] = {"ndcg@10": [round(v, 6) for v in x], "gender_gap": [round(v, 6) for v in y]}
    return {"n_fresh": int(fresh.jd_id.nunique()), "n_test": int(test.jd_id.nunique()), "scorers": rows}


def ablations(results) -> dict:
    out = {}
    for name, (title, held, labels) in ABLATIONS.items():
        m = pd.read_csv(results / f"ablation_{name}" / "metrics.csv")
        ref = load_config(f"configs/ablations/{name}.yaml")["experiment"]["our_method"]
        rows = []
        for s, lab in labels.items():
            rows.append({"id": s, "label": lab, "reference": s == ref,
                         "ndcg@10": _ci(m, s, "test", "original", "ndcg@10"),
                         "frac_nonempty": _ci(m, s, "test", "original", "frac_nonempty"),
                         "gaps": {c: _ci(m, s, "test", c, "abs_gap_norm_changed")
                                  for c in ("pronoun_swap", "name_swap_us", "agentic_communal", "gender_full")}})
        out[name] = {"title": title, "held_fixed": held, "rows": rows}
    return out


def selection(results) -> dict:
    m = pd.read_csv(results / "selection_dev" / "metrics.csv")
    cfg = load_config("configs/selection.yaml")
    rows = []
    for spec in cfg["scorers"]:
        s = spec["name"]
        if not s.startswith("sel_"):
            continue
        ex = spec["extractor"].get("name", spec["extractor"]["type"])
        rows.append({"id": s, "extractor": ex, "backbone": spec["backbone"], "aggregation": spec["aggregation"],
                     "dev_ndcg@10": _ci(m, s, "dev", "original", "ndcg@10")})
    best = max(rows, key=lambda r: r["dev_ndcg@10"][0])
    return {"rule": "highest DEV nDCG@10 (declared before running; fairness not used)", "rows": rows,
            "chosen": best["id"]}


def nearmiss(results) -> dict:
    nm = load_config("configs/ablations/nearmiss.yaml")["nearmiss"]
    dev = pd.read_csv(results / "nearmiss_grid_dev.csv")
    test = pd.read_csv(results / "nearmiss_grid_test.csv")
    eligible = dev[dev["n"] >= int(nm["min_suggestions_dev"])]
    row = eligible.sort_values([nm["select_on"], "n"], ascending=[False, False]).iloc[0]

    def pick(df, lo, hi):
        r = df[(df.lo.round(2) == round(lo, 2)) & (df.hi.round(2) == round(hi, 2))].iloc[0]
        return {"n": int(r.n), "strict": round(float(r.strict), 4), "lenient": round(float(r.lenient), 4),
                "per_pair": round(float(r.per_pair), 3)}

    bands = {}
    for label, (lo, hi) in (("old", nm["backend_band"]), ("chosen", (float(row.lo), float(row.hi)))):
        bands[label] = {"band": [round(lo, 2), round(hi, 2)], "dev": pick(dev, lo, hi), "test": pick(test, lo, hi)}
    grid = [{"lo": round(float(r.lo), 2), "hi": round(float(r.hi), 2), "n": int(r.n),
             "lenient": None if pd.isna(r.lenient) else round(float(r.lenient), 4)} for r in dev.itertuples()]
    return {"bands": bands, "grid_dev": grid, "min_suggestions_dev": int(nm["min_suggestions_dev"])}


def extraction(results) -> dict:
    m = pd.read_csv(results / "extraction" / "metrics.csv")
    m = m[(m.group == "all") & (m.view == "all")]
    rows = [{"extractor": r.extractor, "split": r.split, "mode": r.mode, "precision": round(float(r.precision), 4),
             "recall": round(float(r.recall), 4), "f1": round(float(r.f1), 4)} for r in m.itertuples()]
    return {"rows": rows}


def training() -> dict:
    out = {}
    for seed in (13, 14, 15):
        d = repo_path(f"research/models/jobbert_skillspan/seed{seed}")
        hist = json.loads((d / "history.json").read_text(encoding="utf-8"))
        out[str(seed)] = [{"epoch": h["epoch"], "train_loss": round(h["train_loss"], 5),
                           "dev_exact_f1": round(h["dev_exact_f1"], 4), "dev_partial_f1": round(h["dev_partial_f1"], 4),
                           "seconds": round(h["seconds"], 1)} for h in hist]
    ft = load_config("configs/train_extractor.yaml")["finetune"]
    return {"seeds": out, "base_model": ft["base_model"], "max_epochs": ft["max_epochs"], "patience": ft["patience"],
            "lr": ft["lr"], "batch_size": ft["batch_size"], "select_on": "dev exact span F1"}


def data_stats(proc) -> dict:
    bios = {s: int(len(pd.read_parquet(proc / f"bios_{s}.parquet", columns=["bio_id"]))) for s in ("train", "dev", "test")}
    jds = pd.read_parquet(proc / "jds.parquet", columns=["jd_id", "occupation", "n_words"])
    pools = {s: pd.read_parquet(proc / f"pools_{s}.parquet", columns=["jd_id"]).jd_id.nunique() for s in ("dev", "test")}
    occ = jds.groupby("occupation").size().sort_values(ascending=False)
    cov = {}
    for split in ("dev", "test"):
        p = pd.read_parquet(proc / f"perturbations_{split}.parquet", columns=["condition", "changed"])
        cov[split] = {c: round(float(g.changed.mean() * 100), 1) for c, g in p.groupby("condition")}
    return {"bios": bios, "n_jds": int(len(jds)), "jd_mean_words": round(float(jds.n_words.mean()), 1),
            "pools": {k: int(v) for k, v in pools.items()}, "pool_size": 100, "relevant_per_pool": 10,
            "jds_per_occupation": {k: int(v) for k, v in occ.items()},
            "n_occupations_total": 28, "n_occupations_with_pools": int(len(occ)),
            "perturbation_coverage": cov}


def examples(proc, per_condition: int = 2, window: int = 70) -> list[dict]:
    """A few logged substitutions from DEV counterfactuals, with a little context."""
    p = pd.read_parquet(proc / "perturbations_dev.parquet")
    out = []
    for c in ("gender_full", "name_swap_in", "agentic_communal", "affiliation_swap"):
        sub = p[(p.condition == c) & p.changed].sort_values("bio_id").head(400)
        rng = np.random.default_rng(13)
        for i in rng.permutation(len(sub))[:per_condition]:
            r = sub.iloc[i]
            ch = json.loads(r.changes)
            if not ch:
                continue
            lo = max(0, ch[0]["start_char"] - window)
            hi = min(len(r.text), ch[min(len(ch), 3) - 1]["end_char"] + window)
            out.append({"condition": c, "context": ("…" if lo else "") + r.text[lo:hi] + ("…" if hi < len(r.text) else ""),
                        "changes": [{"from": x["original"], "to": x["replacement"]} for x in ch]})
    return out


def main(argv=None):
    p = base_parser(__doc__, default_config="configs/analysis.yaml")
    args = p.parse_args(argv)
    cfg = setup_run(args)
    results = repo_path(cfg["paths"]["results"])
    if "subset" in cfg["analysis"]["main_dir"]:
        raise SystemExit("export_web only exports FINAL full runs")
    main_dir = repo_path(cfg["analysis"]["main_dir"])
    proc = repo_path(cfg["paths"]["processed_data"])
    meta = json.loads((main_dir / "run_meta.json").read_text(encoding="utf-8"))
    data = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "main_run": {"commit": meta.get("git", {}).get("commit"), "timestamp_utc": meta.get("timestamp_utc")},
        "scorers": [{"id": k, "label": v[0], "family": v[1], "description": v[2]} for k, v in SCORERS.items()],
        "conditions": [{"id": c, "label": CONDITION_LABELS[c]} for c in CONDITIONS],
        "main": main_results(main_dir),
        "fresh_pools": fresh_pools(main_dir, repo_path("research/results/main_subset200"), int(cfg["seed"]),
                                   int(cfg["experiment"]["bootstrap"]["n"])),
        "ablations": ablations(results),
        "selection": selection(results),
        "nearmiss": nearmiss(results),
        "extraction": extraction(results),
        "training": training(),
        "data": data_stats(proc),
        "examples": examples(proc),
        "figures": [],
    }
    out = repo_path(OUT_DIR)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    fig_src = results / "summaries" / "figures"
    for f in FIGURES:
        for ext in ("png", "pdf"):
            shutil.copy2(fig_src / f"{f}.{ext}", out / "figures" / f"{f}.{ext}")
        data["figures"].append(f)
    (out / "data.json").write_text(json.dumps(data, indent=1, allow_nan=False), encoding="utf-8")
    print(f"wrote {out / 'data.json'} and {len(FIGURES)} figures")


if __name__ == "__main__":
    main()
