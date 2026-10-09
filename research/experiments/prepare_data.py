"""Phase 2: prepare BiasBios, job descriptions, the occupation map and candidate pools.

    python -m research.experiments.prepare_data --config configs/data_prep.yaml [--subset N]

Writes (paths from config):
  research/data/processed/bios_{train,dev,test}.parquet
  research/data/processed/jds.parquet, pools_{dev,test}.parquet   (only if JD data present)
  research/data/occupation_map.csv     reviewable title -> occupation map (keeps your reviews)
  research/results/data_stats.md       dataset statistics (also printed)
  research/results/data_prep/run_meta.json

If postings.csv is missing, the BiasBios part still runs and the JD part is reported as
NOT RUN with download instructions.
"""

from __future__ import annotations

import yaml

from research.common.cli import base_parser, setup_run
from research.common.config import RESEARCH_ROOT, repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng
from research.data.biasbios import PROFESSIONS, load_biasbios
from research.data.jobs import load_postings
from research.data.occupation_map import (
    add_review_priority, apply_description_requirements, build_map, compile_patterns, final_mapping, merge_reviews,
)
from research.data.pools import build_pools, select_jds
from research.data.relevance import Relevance


def load_occupations(cfg: dict) -> tuple[dict, list[str]]:
    path = RESEARCH_ROOT / cfg["occupations_file"]
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["occupations"], list(data.get("title_exclude_all") or [])


def bio_stats_md(frames, clean_stats, strategy) -> list[str]:
    lines = ["## BiasBios", "", f"Split strategy: **{strategy}**. Gender is binary in the source data (M/F).", "",
             "| Split | raw | too short | dup in split | overlaps earlier split | kept | % F | mean words | median words |",
             "|---|---|---|---|---|---|---|---|---|"]
    for s, df in frames.items():
        c = clean_stats.get(s, {})
        lines.append(f"| {s} | {c.get('raw', '–')} | {c.get('too_short', '–')} | {c.get('duplicate_in_split', '–')} | "
                     f"{c.get('overlaps_earlier_split', '–')} | {len(df)} | {100 * (df['gender'] == 'F').mean():.1f} | "
                     f"{df['n_words'].mean():.1f} | {df['n_words'].median():.0f} |")
    lines += ["", "### Counts per occupation and gender", "",
              "| Occupation | " + " | ".join(f"{s} F | {s} M" for s in frames) + " | test % F |",
              "|---|" + "---|---|" * len(frames) + "---|"]
    for occ in PROFESSIONS:
        cells = []
        for s, df in frames.items():
            sub = df[df["occupation"] == occ]
            cells += [str((sub["gender"] == "F").sum()), str((sub["gender"] == "M").sum())]
        t = frames["test"][frames["test"]["occupation"] == occ]
        lines.append(f"| {occ} | " + " | ".join(cells) + f" | {100 * (t['gender'] == 'F').mean():.1f} |")
    return lines


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/data_prep.yaml").parse_args(argv)
    cfg = setup_run(args)
    rng = make_rng(int(cfg["seed"]))
    occ_cfg, exclude_all = load_occupations(cfg)
    proc = repo_path(cfg["paths"]["processed_data"])
    proc.mkdir(parents=True, exist_ok=True)
    results = repo_path(cfg["paths"]["results"])

    frames, bstats = load_biasbios(cfg)
    for s, df in frames.items():
        df.to_parquet(proc / f"bios_{s}.parquet", index=False)
    lines = ["# Dataset statistics", ""]
    if cfg.get("subset"):
        lines += [f"**--subset {cfg['subset']}: pools limited to the first {cfg['subset']} JDs per pool set.**", ""]
    lines += bio_stats_md(frames, bstats["cleaning"], bstats["split_strategy"])
    meta_extra = {"biasbios": bstats}

    jcfg, pcfg = cfg["jobs"], cfg["pools"]
    try:
        jds, jstats = load_postings(jcfg["postings_csv"], int(jcfg["min_words"]))
    except FileNotFoundError as e:
        jds = None
        lines += ["", "## Job descriptions: NOT RUN", "", f"- {e}"]
        meta_extra["jobs"] = {"not_run": str(e)}
        print(f"[NOT RUN] job descriptions: {e}")

    if jds is not None:
        patterns = compile_patterns(occ_cfg, exclude_all)
        map_path = repo_path(jcfg["occupation_map_csv"])
        omap = merge_reviews(build_map(jds, patterns), map_path)
        omap = add_review_priority(omap, int(pcfg["jds_per_occupation"]))
        omap.to_csv(map_path, index=False)
        mapping = final_mapping(omap)
        jds["occupation"] = jds["title_norm"].map(mapping)
        jds, desc_dropped = apply_description_requirements(jds, patterns)
        mapped = jds.dropna(subset=["occupation"]).reset_index(drop=True)
        dev_jds, test_jds, coverage = select_jds(mapped, int(pcfg["jds_per_occupation"]),
                                                 int(pcfg["min_jds_per_occupation"]), float(pcfg["jd_dev_fraction"]), rng)
        if cfg.get("subset"):
            dev_jds, test_jds = dev_jds.head(cfg["subset"]), test_jds.head(cfg["subset"])
        rel = Relevance(occ_cfg, cfg["relevance"]["soc_level"])
        pools = {}
        for name, jset in (("dev", dev_jds), ("test", test_jds)):
            bios = frames[pcfg["bio_split_for"][name]]
            pools[name] = build_pools(bios, jset, rel, int(pcfg["n_candidates"]), int(pcfg["n_relevant"]), rng,
                                      pcfg["irrelevant_sampling"])
            pools[name].to_parquet(proc / f"pools_{name}.parquet", index=False)
        used = mapped[mapped["jd_id"].isin(set(dev_jds["jd_id"]) | set(test_jds["jd_id"]))].copy()
        used["pool_set"] = used["jd_id"].map({**{j: "dev" for j in dev_jds["jd_id"]}, **{j: "test" for j in test_jds["jd_id"]}})
        used.to_parquet(proc / "jds.parquet", index=False)

        status_counts = omap["status"].value_counts().to_dict()
        n_unrev_amb = int(((omap["status"] == "ambiguous") & (omap["reviewed_occupation"].str.strip() == "")).sum())
        lines += ["", "## Job descriptions (LinkedIn postings, arshkon, CC BY-SA 4.0)", "",
                  f"Cleaning: {jstats}", "",
                  f"Occupation map: {len(omap)} unique titles matched; status counts {status_counts}; "
                  f"**{n_unrev_amb} ambiguous titles await review** in `{jcfg['occupation_map_csv']}` (excluded until reviewed). "
                  f"High-priority ambiguous titles (candidate occupation short of JDs): "
                  f"{int((omap['review_priority'] == 'high').sum())}. "
                  f"Postings dropped by description requirements: {desc_dropped}. "
                  f"Postings mapped to an occupation: {len(mapped)}.", "",
                  "| Occupation | SOC | postings mapped | JDs used | dev JDs | test JDs | mean JD words (used) |",
                  "|---|---|---|---|---|---|---|"]
        for occ in PROFESSIONS:
            c = coverage.get(occ, {"available": 0, "used": 0, "dev": 0, "test": 0})
            w = used[used["occupation"] == occ]["n_words"]
            lines.append(f"| {occ} | {occ_cfg[occ]['soc']} | {c['available']} | {c['used']} | {c['dev']} | {c['test']} | "
                         f"{w.mean():.0f} |" if len(w) else
                         f"| {occ} | {occ_cfg[occ]['soc']} | {c['available']} | {c['used']} | {c['dev']} | {c['test']} | – |")
        no_pools = [o for o in PROFESSIONS if coverage.get(o, {}).get("used", 0) == 0]
        lines += ["", f"Occupations without pools (too few JDs): {', '.join(no_pools) or 'none'}", "",
                  "## Candidate pools", "",
                  "| Pool set | pools | rows | relevant/pool | % F (all) | % F (relevant) | graded 2 / 1 / 0 |",
                  "|---|---|---|---|---|---|---|"]
        for name, p in pools.items():
            if p.empty:
                lines.append(f"| {name} | 0 | 0 | – | – | – | – |")
                continue
            g = p.groupby("jd_id")
            relp = p[p["rel_binary"] == 1]
            gc = p["rel_graded"].value_counts()
            lines.append(f"| {name} | {g.ngroups} | {len(p)} | {g['rel_binary'].sum().mean():.1f} | "
                         f"{100 * (p['bio_gender'] == 'F').mean():.1f} | {100 * (relp['bio_gender'] == 'F').mean():.1f} | "
                         f"{gc.get(2, 0)} / {gc.get(1, 0)} / {gc.get(0, 0)} |")
        meta_extra.update({"jobs": jstats, "occupation_map_status": status_counts, "coverage": coverage,
                           "description_requirement_dropped": desc_dropped,
                           "n_unreviewed_ambiguous": n_unrev_amb})

    text = "\n".join(lines) + "\n"
    (results / "data_stats.md").write_text(text, encoding="utf-8")
    write_run_metadata(results / "data_prep", cfg, extra=meta_extra)
    print(text)


if __name__ == "__main__":
    main()
