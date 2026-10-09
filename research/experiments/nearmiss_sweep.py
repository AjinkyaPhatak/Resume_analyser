"""Phase 6: sweep the near-miss suggestion band instead of hardcoding 0.35-0.55.

    python -m research.experiments.nearmiss_sweep --config configs/ablations/nearmiss.yaml [--subset N]

The backend suggests "reframe resume phrase R to highlight JD requirement J" when J's best
resume match has cosine similarity in [0.35, 0.55). Whether a suggestion is *right* has no
gold label, so we use an automatic proxy from the ESCO skill hierarchy
(broaderRelationsSkillPillar_en.csv), with both J and R extracted by the ESCO EntityRuler:
  strict  : same ESCO concept, or one is a direct broader concept of the other;
  lenient : strict, or the two share a direct broader concept (siblings).
Precision of a band = share of its suggestions that are correct. The band is chosen on DEV
(highest precision among bands with >= min_suggestions_dev suggestions) and reported on
TEST next to the backend's band, with 95% cluster-bootstrap CIs over JD pools.
This proxy rewards taxonomic closeness only; it can't judge whether a suggestion is
useful to a candidate. Phase 7's human annotation is the better check.

--subset N = N seeded pools per split.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import get_device
from research.experiments.run import select_pools
from research.metrics.stats import bootstrap_ci
from research.scorers.registry import build_encoder, build_extractor_for_scoring


def load_parents(path) -> dict[str, set[str]]:
    b = pd.read_csv(repo_path(path), usecols=["conceptUri", "broaderUri"])
    parents: dict[str, set[str]] = defaultdict(set)
    for c, p in zip(b["conceptUri"], b["broaderUri"]):
        parents[c].add(p)
    return parents


def related(a: str, b: str, parents: dict[str, set[str]], lenient: bool) -> bool:
    if a == b or a in parents.get(b, ()) or b in parents.get(a, ()):
        return True
    return lenient and bool(parents.get(a, set()) & parents.get(b, set()))


def esco_concepts(spans) -> dict[str, str]:
    """ESCO concept URI -> surface text of its first mention (spans in text order)."""
    seen: dict[str, str] = {}
    for s in spans:
        if s.concept_id and s.concept_id not in seen:
            seen[s.concept_id] = s.text
    return seen


def best_matches(pairs: pd.DataFrame, bios: pd.Series, jds: pd.Series, extractor, encoder,
                 parents) -> pd.DataFrame:
    """One row per (pair, JD concept): best resume concept, its similarity, correctness."""
    texts = list(dict.fromkeys(list(bios.loc[pairs["bio_id"]]) + list(jds.loc[pairs["jd_id"]])))
    spans = dict(zip(texts, extractor.extract_batch(texts)))
    con = {t: esco_concepts(spans[t]) for t in texts}
    strings = sorted({v for c in con.values() for v in c.values()})
    vec = dict(zip(strings, encoder.encode(strings))) if strings else {}
    rows = []
    for jd_id, bio_id in zip(pairs["jd_id"], pairs["bio_id"]):
        jc, rc = con[jds[jd_id]], con[bios[bio_id]]
        if not jc or not rc:
            continue
        ju, ru = list(jc), list(rc)
        sim = np.stack([vec[jc[u]] for u in ju]) @ np.stack([vec[rc[u]] for u in ru]).T
        best = sim.argmax(axis=1)
        for i, u in enumerate(ju):
            r = ru[best[i]]
            rows.append({"jd_id": jd_id, "bio_id": bio_id, "jd_concept": u, "resume_concept": r,
                         "sim": float(sim[i, best[i]]),
                         "strict": related(u, r, parents, lenient=False),
                         "lenient": related(u, r, parents, lenient=True)})
    return pd.DataFrame(rows)


def grid(spec):
    start, stop, step = spec
    return np.round(np.arange(start, stop + step / 2, step), 4)


def band_table(m: pd.DataFrame, los, his) -> pd.DataFrame:
    rows = []
    for lo in los:
        for hi in his:
            if hi <= lo:
                continue
            sel = m[(m["sim"] >= lo) & (m["sim"] < hi)]
            rows.append({"lo": lo, "hi": hi, "n": len(sel),
                         "strict": sel["strict"].mean() if len(sel) else np.nan,
                         "lenient": sel["lenient"].mean() if len(sel) else np.nan,
                         "per_pair": len(sel) / max(m.groupby(["jd_id", "bio_id"]).ngroups, 1)})
    return pd.DataFrame(rows)


def band_ci(m: pd.DataFrame, lo: float, hi: float, col: str, n_boot: int, seed: int):
    sel = m[(m["sim"] >= lo) & (m["sim"] < hi)]
    if sel.empty:
        return (np.nan, np.nan, np.nan), 0
    g = sel.groupby("jd_id")[col].agg(["sum", "count"]).to_numpy(float)

    def stat(idx):
        s = g[idx].sum(axis=0)
        return float(s[0] / s[1]) if s[1] else float("nan")

    return bootstrap_ci(n_units=len(g), stat_fn=stat, n_boot=n_boot, seed=seed), len(sel)


# ---------------------------------------------------------------------------- figures

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = {"strict": "#2a78d6", "lenient": "#eb6834"}          # validated categorical slots 1-2
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # blue ramp


def _style(ax):
    ax.set_facecolor("#fcfcfb")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASE)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def plot_curves(m: pd.DataFrame, backend: tuple[float, float], los, his, n_boot: int, seed: int, out_base):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    fig.patch.set_facecolor("#fcfcfb")
    panels = [("lower bound (upper fixed at %.2f)" % backend[1], 0, [(lo, backend[1]) for lo in los if lo < backend[1]]),
              ("upper bound (lower fixed at %.2f)" % backend[0], 1, [(backend[0], hi) for hi in his if hi > backend[0]])]
    for ax, (xlabel, which, bands) in zip(axes, panels):
        _style(ax)
        xs = [b[which] for b in bands]          # which = 0: vary lower bound; 1: vary upper bound
        for col in ("strict", "lenient"):
            est = [band_ci(m, lo, hi, col, n_boot, seed)[0] for lo, hi in bands]
            y = np.array([e[0] for e in est]); lo_ci = np.array([e[1] for e in est]); hi_ci = np.array([e[2] for e in est])
            ax.fill_between(xs, lo_ci, hi_ci, color=SERIES[col], alpha=0.15, linewidth=0)
            ax.plot(xs, y, color=SERIES[col], linewidth=2, marker="o", markersize=4, label=col)
            ok = ~np.isnan(y)
            if ok.any():
                ax.annotate(col, (np.array(xs)[ok][-1], y[ok][-1]), xytext=(4, 0), textcoords="offset points",
                            fontsize=8, color=INK2, va="center")
        ax.axvline(backend[which], color=MUTED, linewidth=1, linestyle="--")
        ax.set_xlabel(xlabel, fontsize=8, color=INK2)
    axes[0].set_ylabel("suggestion precision (ESCO proxy)", fontsize=8, color=INK2)
    axes[0].set_ylim(0, 1)
    axes[1].legend(frameon=False, fontsize=8, labelcolor=INK2, loc="upper left")
    fig.suptitle("Near-miss suggestion precision vs band bounds (test; dashed = backend band)", fontsize=9, color=INK)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{out_base}.{ext}", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_heatmap(tab: pd.DataFrame, col: str, marks: dict, title: str, out_base):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    piv = tab.pivot(index="hi", columns="lo", values=col).sort_index(ascending=False)
    cmap = LinearSegmentedColormap.from_list("blue_seq", SEQ)
    cmap.set_bad("#f0efec")
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    fig.patch.set_facecolor("#fcfcfb")
    im = ax.imshow(piv.to_numpy(float), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(piv.columns)), [f"{v:.2f}" for v in piv.columns], rotation=90, fontsize=7, color=INK2)
    ax.set_yticks(range(len(piv.index)), [f"{v:.2f}" for v in piv.index], fontsize=7, color=INK2)
    ax.set_xlabel("band lower bound", fontsize=8, color=INK2)
    ax.set_ylabel("band upper bound", fontsize=8, color=INK2)
    for s in ax.spines.values():
        s.set_visible(False)
    for label, (lo, hi) in marks.items():
        if lo in piv.columns and hi in piv.index:
            x, y = list(piv.columns).index(lo), list(piv.index).index(hi)
            ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, fill=False, edgecolor=INK, linewidth=1.5))
            ax.annotate(label, (x, y), xytext=(-46, -18), textcoords="offset points", fontsize=8, color=INK,
                        arrowprops={"arrowstyle": "-", "color": INK, "linewidth": 0.8})
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.ax.tick_params(labelsize=7, colors=MUTED, labelcolor=INK2)
    cb.set_label(f"{col} precision", fontsize=8, color=INK2)
    ax.set_title(title, fontsize=9, color=INK)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{out_base}.{ext}", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


# ------------------------------------------------------------------------------- main

def main(argv=None):
    args = base_parser(__doc__, default_config="configs/ablations/nearmiss.yaml").parse_args(argv)
    cfg = setup_run(args)
    nm = cfg["nearmiss"]
    seed, n_boot = int(cfg["seed"]), int(cfg["experiment"]["bootstrap"]["n"])
    proc = repo_path(cfg["paths"]["processed_data"])
    parents = load_parents(nm["hierarchy_csv"])
    extractor = build_extractor_for_scoring(nm["extractor"], cfg)
    encoder = build_encoder(cfg["backbones"][nm["backbone"]], cfg, get_device(cfg.get("device", "auto")))
    jds = pd.read_parquet(proc / "jds.parquet").set_index("jd_id")["text"]
    los, his = grid(nm["lo_grid"]), grid(nm["hi_grid"])
    backend = tuple(float(x) for x in nm["backend_band"])

    matches, tabs = {}, {}
    for split in ("dev", "test"):
        pools = select_pools(pd.read_parquet(proc / f"pools_{split}.parquet"), cfg.get("subset"), seed)
        if nm["pairs"] == "relevant":
            pools = pools[pools["rel_binary"] == 1]
        bios = pd.read_parquet(proc / f"bios_{split}.parquet").set_index("bio_id")["text"]
        matches[split] = best_matches(pools, bios, jds, extractor, encoder, parents)
        tabs[split] = band_table(matches[split], los, his)
        print(f"[{split}] {len(pools)} pairs, {len(matches[split])} JD-concept best matches", flush=True)

    dev = tabs["dev"]
    eligible = dev[dev["n"] >= int(nm["min_suggestions_dev"])]
    chosen_row = eligible.sort_values([nm["select_on"], "n"], ascending=[False, False]).iloc[0]
    chosen = (float(chosen_row["lo"]), float(chosen_row["hi"]))

    lines = ["# Near-miss suggestion band sweep", ""]
    if cfg.get("subset"):
        lines += [f"**PRELIMINARY: --subset {cfg['subset']} pools per split.**", ""]
    lines += ["Suggestion = a JD skill whose best resume match has cosine similarity in [lo, hi) "
              f"(ESCO EntityRuler entities, {nm['backbone']} embeddings, {nm['pairs']} bio-JD pairs). "
              "Precision proxy from the ESCO hierarchy: *strict* = same concept or direct parent/child; "
              "*lenient* = strict or siblings. The band is chosen on DEV (max "
              f"{nm['select_on']} precision with >= {nm['min_suggestions_dev']} dev suggestions) and evaluated on TEST. "
              "95% CIs: cluster bootstrap over JD pools.", "",
              "| Band | split | suggestions | per pair | strict precision | lenient precision |",
              "|---|---|---|---|---|---|"]
    for label, band in (("backend 0.35-0.55", backend), (f"chosen {chosen[0]:.2f}-{chosen[1]:.2f}", chosen)):
        for split in ("dev", "test"):
            (s, s_lo, s_hi), n = band_ci(matches[split], band[0], band[1], "strict", n_boot, seed)
            (l, l_lo, l_hi), _ = band_ci(matches[split], band[0], band[1], "lenient", n_boot, seed)
            per = n / max(matches[split].groupby(["jd_id", "bio_id"]).ngroups, 1)
            lines.append(f"| {label} | {split} | {n} | {per:.2f} | {s:.3f} [{s_lo:.3f}, {s_hi:.3f}] | "
                         f"{l:.3f} [{l_lo:.3f}, {l_hi:.3f}] |")
    for split in ("dev", "test"):
        m = matches[split]
        lines += ["", f"Base rates ({split}): share of ALL best matches that are correct -- strict "
                  f"{m['strict'].mean():.3f}, lenient {m['lenient'].mean():.3f} (n = {len(m)})."]
    fig_dir = repo_path(nm["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_subset{cfg['subset']}" if cfg.get("subset") else ""
    plot_curves(matches["test"], backend, los, his, n_boot, seed, fig_dir / f"nearmiss_curves{tag}")
    plot_heatmap(dev, nm["select_on"], {"backend": backend, "chosen": chosen},
                 f"DEV {nm['select_on']} precision by band (grey = invalid band, upper <= lower)",
                 fig_dir / f"nearmiss_heatmap_dev{tag}")
    lines += ["", f"Figures: `{nm['figures_dir']}/nearmiss_curves{tag}.(pdf|png)`, "
              f"`nearmiss_heatmap_dev{tag}.(pdf|png)`."]
    out = repo_path(cfg["paths"]["results"]) / f"nearmiss_sweep{tag}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for split, t in tabs.items():
        t.to_csv(repo_path(cfg["paths"]["results"]) / f"nearmiss_grid_{split}{tag}.csv", index=False)
    write_run_metadata(repo_path(cfg["paths"]["results"]) / f"nearmiss{tag}", cfg, extra={"chosen_band": chosen})
    print("\n".join(lines))


if __name__ == "__main__":
    main()
