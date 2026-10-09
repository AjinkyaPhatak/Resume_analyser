"""LaTeX (booktabs) tables generated directly from results CSVs: no hand-copied numbers.

Requires \\usepackage{booktabs} (and graphicx for \\resizebox) in the paper.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .figures import metric_row

_TEX = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(text: str) -> str:
    return "".join(_TEX.get(c, c) for c in str(text))


def ci(v: float, lo: float, hi: float, digits: int = 3) -> str:
    if np.isnan(v):
        return "--"
    if np.isnan(lo) or np.isnan(hi):
        return f"{v:.{digits}f}"
    return f"{v:.{digits}f}\\,{{\\scriptsize[{lo:.{digits}f}, {hi:.{digits}f}]}}"


def _wrap(body: list[str], colspec: str, caption: str, label: str, resize: bool = True) -> str:
    tab = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", *body, "\\bottomrule", "\\end{tabular}"]
    inner = ["\\resizebox{\\textwidth}{!}{%", *tab, "}"] if resize else tab
    return "\n".join(["\\begin{table*}[t]", "\\centering", *inner, f"\\caption{{{caption}}}",
                      f"\\label{{{label}}}", "\\end{table*}", ""])


def _sig(tests: pd.DataFrame, condition: str, metric: str, baseline: str, alpha: float = 0.05) -> str:
    if tests is None or tests.empty:
        return ""
    t = tests[(tests.condition == condition) & (tests.metric == metric) & (tests.baseline == baseline)]
    return "$^{\\dagger}$" if len(t) and t.iloc[0]["p_holm"] < alpha else ""


def main_tables(metrics: pd.DataFrame, tests: pd.DataFrame, acfg: dict, preliminary: bool) -> str:
    ours = acfg["our_method"]
    scorers = list(dict.fromkeys(metrics["scorer"]))
    name = lambda s: (f"\\textbf{{{esc(acfg['display'].get(s, s))}}}" if s == ours  # noqa: E731
                      else esc(acfg["display"].get(s, s)))
    pre = "PRELIMINARY. " if preliminary else ""
    # accuracy
    body = ["Scorer & nDCG@10 & MRR & P@5 & P@10 \\\\", "\\midrule"]
    for s in scorers:
        cells = [ci(*metric_row(metrics, s, "original", m)) for m in ("ndcg@10", "mrr", "p@5", "p@10")]
        if s != ours:
            cells[0] += _sig(tests, "original", "ndcg@10", s)
        body.append(f"{name(s)} & " + " & ".join(cells) + " \\\\")
    acc = _wrap(body, "lcccc", pre + "Ranking accuracy on test pools (mean over JD pools, 95\\% cluster-bootstrap CI). "
                f"$^\\dagger$: differs from {esc(acfg['display'].get(ours, ours))} (paired permutation test, Holm $p<0.05$).",
                "tab:accuracy")
    # fairness
    conds = acfg["bar_conditions"]
    body = ["Scorer & " + " & ".join(esc(acfg["condition_display"].get(c, c)) for c in conds) + " \\\\", "\\midrule"]
    for s in scorers:
        cells = []
        for c in conds:
            cell = ci(*metric_row(metrics, s, c, "abs_gap_norm_changed"))
            if s != ours:
                cell += _sig(tests, c, "abs_gap_norm_changed", s)
            cells.append(cell)
        body.append(f"{name(s)} & " + " & ".join(cells) + " \\\\")
    fair = _wrap(body, "l" + "c" * len(conds),
                 pre + "Counterfactual $|$score gap$|$ (normalised by the SD of original scores in the pool; "
                 "changed bios only; lower = less leakage). $^\\dagger$ as in Table~\\ref{tab:accuracy}.", "tab:fairness")
    # signed
    body = ["Scorer & " + " & ".join(esc(acfg["condition_display"].get(c, c)) for c in conds) + " \\\\", "\\midrule"]
    for s in scorers:
        body.append(f"{name(s)} & " + " & ".join(ci(*metric_row(metrics, s, c, "signed_gap_norm_changed")) for c in conds) + " \\\\")
    signed = _wrap(body, "l" + "c" * len(conds),
                   pre + "Signed normalised gap: positive = the scorer favours the female-coded "
                   "(agentic/communal: communal; same-gender Indian name: Indian-name) version.", "tab:signed")
    return "\n".join([acc, fair, signed])


def extraction_table(csv_path) -> str:
    m = pd.read_csv(csv_path)
    m = m[(m.group == "all") & (m.view == "all") & (m.split == "test")]
    rows = ["Extractor & Exact P & Exact R & Exact F1 & Partial F1 \\\\", "\\midrule"]
    seeds = m[m.extractor.str.startswith("jobbert_ft_s")]
    for ex in [e for e in dict.fromkeys(m.extractor) if not e.startswith("jobbert_ft_s")]:
        e = m[(m.extractor == ex) & (m["mode"] == "exact")].iloc[0]
        p = m[(m.extractor == ex) & (m["mode"] == "partial")].iloc[0]
        rows.append(f"{esc(ex)} & {e.precision:.3f} & {e.recall:.3f} & {e.f1:.3f} & {p.f1:.3f} \\\\")
    if len(seeds):
        def ms(mode, col):
            v = seeds[seeds["mode"] == mode][col].to_numpy()
            return f"{v.mean():.3f}$\\pm${v.std(ddof=1):.3f}" if len(v) > 1 else f"{v.mean():.3f}"
        rows.append(f"fine-tuned JobBERT ({seeds.extractor.nunique()} seeds) & {ms('exact', 'precision')} & "
                    f"{ms('exact', 'recall')} & {ms('exact', 'f1')} & {ms('partial', 'f1')} \\\\")
    return _wrap(rows, "lcccc", "Span-level skill extraction on the SkillSpan test split (skill $\\cup$ knowledge). "
                 "Partial = overlap of at least one token.", "tab:extraction", resize=False)


def ablation_table(dirs: dict, acfg: dict, preliminary: bool) -> str:
    conds = ["pronoun_swap", "name_swap_us", "agentic_communal", "gender_full"]
    head = "Variant & nDCG@10 & " + " & ".join(esc(acfg["condition_display"][c]) for c in conds) + " \\\\"
    body = [head]
    for abl, d in dirs.items():
        from pathlib import Path

        f = Path(d) / "metrics.csv"
        if not f.exists():
            continue
        m = pd.read_csv(f)
        body += ["\\midrule", f"\\multicolumn{{{len(conds) + 2}}}{{l}}{{\\textit{{{esc(abl.replace('_', ' '))}}}}} \\\\"]
        for s in dict.fromkeys(m.scorer):
            cells = [ci(*metric_row(m, s, "original", "ndcg@10"), digits=3)]
            cells += [ci(*metric_row(m, s, c, "abs_gap_norm_changed")) for c in conds]
            body.append(f"\\quad {esc(s)} & " + " & ".join(cells) + " \\\\")
    pre = "PRELIMINARY. " if preliminary else ""
    return _wrap(body, "l" + "c" * (len(conds) + 1),
                 pre + "Ablations (test): ranking accuracy and normalised counterfactual $|$gap$|$.", "tab:ablations")


def selection_table(sel_dir, ours_variant: str | None) -> str:
    from pathlib import Path

    m = pd.read_csv(Path(sel_dir) / "metrics.csv")
    m = m[(m.split == "dev") & (m.condition == "original") & (m.metric == "ndcg@10")].sort_values("value", ascending=False)
    body = ["Candidate (dev only) & nDCG@10 \\\\", "\\midrule"]
    for r in m.itertuples():
        mark = " (selected)" if r.scorer == ours_variant else ""
        body.append(f"{esc(r.scorer)}{mark} & {ci(r.value, r.ci_low, r.ci_high)} \\\\")
    return _wrap(body, "lc", "Pre-declared dev-only selection of the main entity-level configuration "
                 "(highest dev nDCG@10; fairness metrics not used).", "tab:selection", resize=False)
