"""Extra figures for the project report, drawn from the web export of the FINAL runs.

    python -m research.analysis.report_figures

Reads frontend/public/research/data.json (written by research.analysis.export_web) and
writes research/results/summaries/figures/report_*.png: the method pipeline, extraction
F1, tagger training curves, dev-only selection and the held-out check.
Same palette and conventions as figures.py (colour = family; labels carry identity).
"""

from __future__ import annotations

import json

from research.analysis.figures import BASE, FAMILY_COLORS, INK, INK2, MUTED, SURFACE, _plt, _style
from research.common.config import repo_path

OUT = "research/results/summaries/figures"
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#898781"
FAMILY = {"entity": FAMILY_COLORS["ours"], "full-text": FAMILY_COLORS["neural"],
          "lexical": FAMILY_COLORS["lexical"], "legacy": FAMILY_COLORS["deployed"]}


def _save(fig, name):
    path = repo_path(OUT) / f"report_{name}.png"
    fig.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", path)


def pipeline(plt):
    fig, ax = plt.subplots(figsize=(9.6, 2.5))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axis("off")
    ax.set_xlim(-0.5, 100.5)
    ax.set_ylim(0, 26)
    boxes = [(0, "Resume\nJob description", False),
             (15.5, "Extract entities (union)\n\u2022 fine-tuned JobBERT tagger\n\u2022 ESCO EntityRuler\n\u2022 filtered noun chunks", True),
             (39.5, "Keep skill +\nknowledge spans", False), (56.5, "JobBERT-v2\nentity embeddings", False),
             (73.5, "JD \u00d7 resume\ncosine matrix", False), (87.5, "IDF-weighted\nMaxSim \u2192 score", False)]
    widths = [12.5, 21, 14, 14, 11, 12.5]
    for (x, text, hl), w in zip(boxes, widths):
        ax.add_patch(plt.Rectangle((x, 5), w, 16, facecolor="#cde2fb" if hl else "white",
                                   edgecolor=BLUE if hl else BASE, linewidth=1.2))
        ax.text(x + w / 2, 13, text, ha="center", va="center", fontsize=7.2, color=INK, linespacing=1.4)
    for (x, _, _), w, (nx, _, _) in zip(boxes, widths, boxes[1:]):
        ax.annotate("", xy=(nx - 0.3, 13), xytext=(x + w + 0.3, 13),
                    arrowprops={"arrowstyle": "->", "color": MUTED, "linewidth": 1})
    ax.text(0, 1.2, "Late interaction over extracted skill entities (cf. ColBERT, BERTScore). "
                    "Names, pronouns and most wording never become entities.", fontsize=7.5, color=INK2)
    _save(fig, "pipeline")


def extraction(plt, d):
    rows = [r for r in d["extraction"]["rows"] if r["split"] == "test"]
    names = [("noun_chunk", "Noun chunks (old app)"), ("filtered_nc", "Filtered noun chunks"),
             ("esco", "ESCO EntityRuler"), ("esco+nc", "ESCO + noun chunks"),
             ("jobbert_ft_s13", "JobBERT fine-tuned, seed 13"), ("jobbert_ft_s14", "JobBERT fine-tuned, seed 14"),
             ("jobbert_ft_s15", "JobBERT fine-tuned, seed 15")]
    f1 = lambda e, m: next(r["f1"] for r in rows if r["extractor"] == e and r["mode"] == m)  # noqa: E731
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    ax.grid(axis="y", visible=False)
    h = 0.36
    for i, (e, _) in enumerate(names):
        y = len(names) - 1 - i
        for off, mode, col in ((h / 2 + 0.02, "exact", BLUE), (-h / 2 - 0.02, "partial", ORANGE)):
            v = f1(e, mode)
            ax.barh(y + off, v, height=h, color=col, label=f"{mode}-match F1" if i == 0 else None)
            ax.text(v + 0.012, y + off, f"{v:.3f}", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([n for _, n in reversed(names)], fontsize=8, color=INK)
    ax.set_xlim(0, 1)
    ax.set_xlabel("SkillSpan test F1", fontsize=8, color=INK2)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right")
    _save(fig, "extraction_f1")


def training(plt, d):
    seeds = d["training"]["seeds"]
    cols = dict(zip(sorted(seeds), (BLUE, ORANGE, AQUA)))
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.3))
    fig.patch.set_facecolor(SURFACE)
    for ax, key, label in ((axes[0], "dev_exact_f1", "dev exact span F1"), (axes[1], "train_loss", "training loss")):
        _style(ax)
        for s in sorted(seeds):
            xs = [h["epoch"] for h in seeds[s]]
            ys = [h[key] for h in seeds[s]]
            ax.plot(xs, ys, color=cols[s], linewidth=2, marker="o", markersize=3.5, label=f"seed {s}")
            if key == "dev_exact_f1":
                b = max(seeds[s], key=lambda h: h["dev_exact_f1"])
                ax.plot([b["epoch"]], [b[key]], marker="o", markersize=11, markerfacecolor="none",
                        markeredgecolor=cols[s], markeredgewidth=1.4)
        ax.set_xlabel("epoch", fontsize=8, color=INK2)
        ax.set_ylabel(label, fontsize=8, color=INK2)
        ax.set_xticks(range(1, 11))
    axes[0].legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right")
    axes[0].set_title("Circles mark the epoch kept (best dev exact F1)", fontsize=8, color=INK2, loc="left")
    _save(fig, "training_curves")


def selection(plt, d):
    rows = sorted(d["selection"]["rows"], key=lambda r: r["dev_ndcg@10"][0])
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    ax.grid(axis="y", visible=False)
    labels = []
    for i, r in enumerate(rows):
        m, lo, hi = r["dev_ndcg@10"]
        chosen = r["id"] == d["selection"]["chosen"]
        ax.barh(i, m, height=0.6, color=BLUE if chosen else GREY)
        ax.plot([lo, hi], [i, i], color=INK2, linewidth=1.2)
        ax.text(hi + 0.008, i, f"{m:.3f}", va="center", fontsize=7.5, color=INK, fontweight="bold" if chosen else None)
        ex = "JobBERT+ESCO+NC" if r["extractor"].startswith("jobbert") else "ESCO+NC"
        bb = "JobBERT-v2" if r["backbone"] == "jobbert_v2" else "MiniLM"
        labels.append(f"{ex} · {bb} · {'IDF' if r['aggregation'] == 'idf_weighted' else 'mean'}")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=8, color=INK)
    ax.set_xlim(0, 0.72)
    ax.set_xlabel("dev nDCG@10 (line = 95% CI); blue = chosen by the pre-declared rule", fontsize=8, color=INK2)
    _save(fig, "selection_dev")


def heldout(plt, d):
    fam = {s["id"]: s["family"] for s in d["scorers"]}
    lab = {s["id"]: s["label"] for s in d["scorers"]}
    f = d["fresh_pools"]
    rows = sorted(f["scorers"].items(), key=lambda kv: -kv[1]["gender_gap"][0])
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    ax.grid(axis="y", visible=False)
    for i, (s, v) in enumerate(rows):
        m, lo, hi = v["gender_gap"]
        ax.plot([lo, hi], [i, i], color=FAMILY[fam[s]], linewidth=2)
        ax.plot([m], [i], marker="o", markersize=7, color=FAMILY[fam[s]], markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(hi + 0.008, i, f"{m:.3f}", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([lab[s] for s, _ in rows], fontsize=8, color=INK)
    ax.set_xlim(left=-0.005)
    ax.set_xlabel(f"|score change| under the full gender flip, {f['n_fresh']} untouched test pools (pool SDs, 95% CI)",
                  fontsize=8, color=INK2)
    _save(fig, "heldout")


def main():
    plt = _plt()
    d = json.loads((repo_path("frontend/public/research") / "data.json").read_text(encoding="utf-8"))
    pipeline(plt)
    extraction(plt, d)
    training(plt, d)
    selection(plt, d)
    heldout(plt, d)


if __name__ == "__main__":
    main()
