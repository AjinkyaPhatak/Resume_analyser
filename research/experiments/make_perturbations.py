"""Phase 4: generate counterfactual versions of every pooled bio.

    python -m research.experiments.make_perturbations --config configs/perturbations.yaml [--subset N]

For each split with pools (dev, test), every bio that appears in a pool is parsed once
with spaCy and every condition in the config is applied to that parse.

Writes:
  data/processed/perturbations_{dev,test}.parquet   bio_id, condition, text, changed, n_changes, changes (JSON)
  data/processed/name_pools.json                    the exact name pools used
  results/perturbation_samples.md                   50 changed dev examples per condition (for manual QA)
  results/perturbation_stats.md                     coverage: % of bios changed, per condition/split/gender
  results/perturbations/run_meta.json
--subset N keeps the first N pooled bios (seeded order) per split.
"""

from __future__ import annotations

import json
import time

import pandas as pd
import spacy

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng
from research.perturbations.registry import build_conditions, build_parts


def highlight(text: str, spans: list[tuple[int, int]]) -> str:
    """Wrap char spans in **bold** (spans sorted, non-overlapping)."""
    out, i = [], 0
    for s, e in sorted(spans):
        out.append(text[i:s]); out.append("**" + text[s:e] + "**"); i = e
    out.append(text[i:])
    return "".join(out).replace("\n", " ")


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/perturbations.yaml").parse_args(argv)
    cfg = setup_run(args)
    proc = repo_path(cfg["paths"]["processed_data"])
    res_dir = repo_path(cfg["paths"]["results"])
    nlp = spacy.load(cfg["spacy_model"])
    parts = build_parts(cfg, nlp)
    conditions = build_conditions(cfg, parts)
    names = parts["_name_resources"]
    (proc / "name_pools.json").write_text(json.dumps(names.pools, indent=2), encoding="utf-8")

    stats_rows, samples_by_cond, meta = [], {}, {}
    for split in ("dev", "test"):
        pools = pd.read_parquet(proc / f"pools_{split}.parquet")
        bios = pd.read_parquet(proc / f"bios_{split}.parquet").set_index("bio_id")
        ids = sorted(pools["bio_id"].unique())
        if cfg.get("subset"):
            order = make_rng(int(cfg["seed"])).permutation(len(ids))
            ids = sorted(ids[i] for i in order[: cfg["subset"]])
        sub = bios.loc[ids]
        t0 = time.perf_counter()
        rows = []
        for bio_id, gender, doc in zip(ids, sub["gender"], nlp.pipe(sub["text"].tolist(), batch_size=256)):
            for cond in conditions:
                r = cond.apply(doc, gender, bio_id)
                rows.append({"bio_id": bio_id, "condition": cond.name, "text": r.text, "changed": r.changed,
                             "n_changes": len(r.changes), "changes": r.changes_json()})
        out = pd.DataFrame(rows)
        out.to_parquet(proc / f"perturbations_{split}.parquet", index=False)
        meta[split] = {"n_bios": len(ids), "seconds": round(time.perf_counter() - t0, 1)}
        print(f"[{split}] {len(ids)} bios x {len(conditions)} conditions in {meta[split]['seconds']}s", flush=True)

        g = out.merge(sub[["gender", "occupation"]], left_on="bio_id", right_index=True)
        for cond, gc in g.groupby("condition", sort=False):
            row = {"split": split, "condition": cond, "bios": len(gc), "% changed": 100 * gc["changed"].mean(),
                   "% changed F": 100 * gc.loc[gc["gender"] == "F", "changed"].mean(),
                   "% changed M": 100 * gc.loc[gc["gender"] == "M", "changed"].mean(),
                   "mean changes | changed": gc.loc[gc["changed"], "n_changes"].mean() if gc["changed"].any() else 0.0}
            stats_rows.append(row)
        if split == cfg["samples"]["split"]:
            rng = make_rng(int(cfg["seed"]) + 1)
            n = int(cfg["samples"]["n_per_condition"])
            for cond in [c.name for c in conditions]:
                ch = g[(g["condition"] == cond) & g["changed"]].reset_index(drop=True)
                pick = sorted(rng.permutation(len(ch))[: n]) if len(ch) else []
                samples_by_cond[cond] = [(ch.loc[i, "bio_id"], ch.loc[i, "gender"], sub.loc[ch.loc[i, "bio_id"], "text"],
                                          ch.loc[i, "text"], json.loads(ch.loc[i, "changes"])) for i in pick]
                samples_by_cond[cond + "__available"] = len(ch)

    stats = pd.DataFrame(stats_rows)
    lines = ["# Perturbation coverage", ""]
    if cfg.get("subset"):
        lines += [f"**--subset {cfg['subset']} bios per split.**", ""]
    lines += ["Share of pooled bios that each condition actually changes (unchanged bios have an "
              "identical counterfactual, so their score gap is 0 by construction).", "",
              "| split | condition | bios | % changed | % changed F | % changed M | mean changes when changed |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {r.split} | {r.condition} | {r.bios} | {r[3]:.1f} | {r[4]:.1f} | {r[5]:.1f} | {r[6]:.2f} |"
              for r in stats.itertuples(index=False)]
    lines += ["", "## Name pools", ""] + [f"- **{p} {g}** ({len(v)}): {', '.join(v[:40])}{' ...' if len(v) > 40 else ''}"
                                          for p, d in names.pools.items() for g, v in d.items()]
    (res_dir / "perturbation_stats.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    sl = ["# Perturbation samples for manual review", "",
          f"Up to {cfg['samples']['n_per_condition']} randomly chosen *changed* bios per condition "
          f"({cfg['samples']['split']} split, seed {int(cfg['seed']) + 1}). Changed words are **bold** in both "
          "versions. Check that meaning is preserved and the text is grammatical; note problems by bio_id.", ""]
    for cond in [c.name for c in conditions]:
        items = samples_by_cond.get(cond, [])
        sl += [f"## {cond} ({len(items)} shown of {samples_by_cond.get(cond + '__available', 0)} changed)", ""]
        for k, (bio_id, gender, before, after, changes) in enumerate(items, 1):
            sl += [f"### {cond} #{k}: `{bio_id}` (gender {gender})", "",
                   "- before: " + highlight(before, [(c["orig_start"], c["orig_end"]) for c in changes]),
                   "- after:  " + highlight(after, [(c["start_char"], c["end_char"]) for c in changes]),
                   "- changes: " + "; ".join(f"{c['original']} -> {c['replacement']} [{c['kind']}]" for c in changes), ""]
    (res_dir / "perturbation_samples.md").write_text("\n".join(sl) + "\n", encoding="utf-8")
    write_run_metadata(res_dir / "perturbations", cfg, extra={"splits": meta})
    print("\n".join(lines))


if __name__ == "__main__":
    main()
