"""Paper figures, drawn straight from a results directory's metrics.csv.

Colour encodes scorer FAMILY (ours / neural full-text / lexical / deployed backend), using
dataviz categorical slots 1-3 (validated all-pairs for scatter) plus a neutral grey;
every scorer is identified by a direct label, so identity never depends on colour.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

INK, INK2, MUTED, GRID, BASE, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
FAMILY_COLORS = {"ours": "#2a78d6", "neural": "#eb6834", "lexical": "#1baf7a", "deployed": "#898781"}
FAMILY_LABELS = {"ours": "Entity-level (ours)", "neural": "Full-text neural", "lexical": "Lexical",
                 "deployed": "Deployed backend"}


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASE)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def family_of(scorer: str, families: dict) -> str:
    for fam, members in families.items():
        if scorer in members:
            return fam
    return "neural"


def metric_row(metrics: pd.DataFrame, scorer: str, condition: str, metric: str, split: str = "test"):
    m = metrics[(metrics.scorer == scorer) & (metrics.split == split) & (metrics.condition == condition)
                & (metrics.metric == metric)]
    if m.empty:
        return np.nan, np.nan, np.nan
    r = m.iloc[0]
    return float(r["value"]), float(r["ci_low"]), float(r["ci_high"])


def headline_scatter(metrics: pd.DataFrame, acfg: dict, out_base, preliminary: bool = False) -> pd.DataFrame:
    """x = nDCG@10, y = |gap| under the headline condition; CI bars both ways."""
    plt = _plt()
    h = acfg["headline"]
    scorers = list(dict.fromkeys(metrics["scorer"]))
    rows = []
    for s in scorers:
        x = metric_row(metrics, s, "original", h["x_metric"])
        y = metric_row(metrics, s, h["y_condition"], h["y_metric"])
        if not np.isnan(x[0]) and not np.isnan(y[0]):
            rows.append({"scorer": s, "x": x[0], "x_lo": x[1], "x_hi": x[2], "y": y[0], "y_lo": y[1], "y_hi": y[2],
                         "family": family_of(s, acfg["families"])})
    pts = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    for fam in FAMILY_COLORS:
        sub = pts[pts.family == fam]
        if sub.empty:
            continue
        ax.errorbar(sub.x, sub.y, xerr=[sub.x - sub.x_lo, sub.x_hi - sub.x], yerr=[sub.y - sub.y_lo, sub.y_hi - sub.y],
                    fmt="none", ecolor=FAMILY_COLORS[fam], elinewidth=1, alpha=0.6, capsize=0)
        ax.scatter(sub.x, sub.y, s=70 if fam == "ours" else 48, color=FAMILY_COLORS[fam], edgecolors=SURFACE,
                   linewidths=1.5, zorder=3, label=FAMILY_LABELS[fam])
    xr = (pts.x.max() - pts.x.min()) or 1.0
    yr = (pts.y.max() - pts.y.min()) or 1.0
    placed = []                                           # simple collision avoidance for direct labels
    for r in pts.sort_values("x").itertuples():
        offset = (6, 4)
        if any(abs(r.x - px) < 0.12 * xr and abs(r.y - py) < 0.06 * yr and po == (6, 4) for px, py, po in placed):
            offset = (6, 16)                              # stack above rather than under (points can sit on y=0)
        placed.append((r.x, r.y, offset))
        ax.annotate(acfg["display"].get(r.scorer, r.scorer), (r.x, r.y), xytext=offset, textcoords="offset points",
                    fontsize=8, color=INK if r.family == "ours" else INK2,
                    fontweight="bold" if r.family == "ours" else "normal")
    ax.set_xlabel("Ranking accuracy: nDCG@10 (test, higher is better)", fontsize=9, color=INK2)
    cond = acfg["condition_display"].get(h["y_condition"], h["y_condition"])
    ax.set_ylabel(f"Counterfactual |score gap| under {cond.lower()}\n(SD-normalised, lower is better)",
                  fontsize=9, color=INK2)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="upper left")
    title = "Accuracy vs demographic leakage (95% cluster-bootstrap CIs)"
    ax.set_title(("PRELIMINARY - " if preliminary else "") + title, fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{out_base}.{ext}", dpi=220, facecolor=SURFACE)
    plt.close(fig)
    return pts


def perturbation_bars(metrics: pd.DataFrame, acfg: dict, out_base, metric: str = "abs_gap_norm_changed",
                      preliminary: bool = False) -> None:
    """Small multiples: one panel per perturbation, one horizontal bar per scorer (+ CI)."""
    plt = _plt()
    conds = [c for c in acfg["bar_conditions"] if (metrics.condition == c).any()]
    scorers = list(dict.fromkeys(metrics["scorer"]))
    ncol = 4
    nrow = int(np.ceil(len(conds) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(10, 2.0 + 1.9 * nrow), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    axes = np.atleast_1d(axes).ravel()
    ypos = np.arange(len(scorers))[::-1]
    for ax, cond in zip(axes, conds):
        _style(ax)
        ax.grid(True, axis="x", color=GRID, linewidth=0.6)
        ax.grid(False, axis="y")
        for yi, s in zip(ypos, scorers):
            v, lo, hi = metric_row(metrics, s, cond, metric)
            if np.isnan(v):
                continue
            color = FAMILY_COLORS[family_of(s, acfg["families"])]
            ax.barh(yi, v, height=0.62, color=color, edgecolor=SURFACE, linewidth=1)
            ax.plot([lo, hi], [yi, yi], color=INK2, linewidth=1)
        ax.set_title(acfg["condition_display"].get(cond, cond), fontsize=9, color=INK, loc="left")
        ax.set_xlim(left=0)
        ax.set_yticks(ypos, [acfg["display"].get(s, s) for s in scorers], fontsize=8)
    for ax in axes[len(conds):]:
        ax.set_axis_off()
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in FAMILY_COLORS.values()]
    host = axes[len(conds)] if len(conds) < len(axes) else axes[-1]   # legend in the first empty panel
    host.legend(handles, list(FAMILY_LABELS.values()), loc="center", frameon=False, fontsize=9,
                labelcolor=INK2, title="Scorer family", title_fontsize=9)
    fig.suptitle(("PRELIMINARY - " if preliminary else "") +
                 "Counterfactual |score gap| by perturbation (SD-normalised, changed bios; bars = mean, lines = 95% CI)",
                 fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    for ext in ("pdf", "png"):
        fig.savefig(f"{out_base}.{ext}", dpi=220, facecolor=SURFACE)
    plt.close(fig)
