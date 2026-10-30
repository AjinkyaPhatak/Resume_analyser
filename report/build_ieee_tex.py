"""Compile the project report with IEEE's official LaTeX class (IEEEtran, conference mode).

    venv/Scripts/python.exe report/build_ieee_tex.py

Reads report/report.md (the report's Markdown export), writes report/ieee/paper.tex plus
its figures, and compiles it with Tectonic (a self-contained XeLaTeX engine; set TECTONIC
or install it at %LOCALAPPDATA%/tectonic/tectonic.exe). Output: Project_Report_IEEE.pdf in
the repo root.

Only FORMAT and HEADINGS change: the text, numbers, tables and figures are the report's own.
Section headings are renamed to conventional IEEE paper headings (HEADINGS below), section 4
is split into "System Design and Methodology" and "Results and Discussion" at the same point
in the text, cross-references are renumbered to match, and author-year citations become
numbered IEEE citations.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import build_ieee as base          # citation map, reference entries, figure and table lists

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = HERE / "ieee"
OUT_PDF = ROOT / "Project_Report_IEEE.pdf"
TECTONIC = Path(os.environ.get("TECTONIC", Path(os.environ.get("LOCALAPPDATA", "")) / "tectonic" / "tectonic.exe"))

TITLE = "Fairness Audit of Entity-Level Resume Matching"
AUTHOR = ("Ajinkya Phatak", "Registration No. 23BCE0643")

# old heading -> (level, new heading); level 1 = \section, 2 = \subsection
HEADINGS = {
    "1. Introduction": (1, "Introduction"),
    "1.1 The problem": (2, "Motivation"),
    "1.2 Where this project started": (2, "Baseline System"),
    "1.3 What we did": (2, "Approach Overview"),
    "1.4 Contributions": (2, "Contributions"),
    "2. Literature review": (1, "Related Work"),
    "2.1 Resume\u2013job matching": (2, "Resume\u2013Job Matching"),
    "2.2 Late interaction": (2, "Late-Interaction Retrieval"),
    "2.3 Skill extraction": (2, "Skill Extraction"),
    "2.4 Bias in hiring and in language models": (2, "Bias in Hiring and Language Models"),
    "2.5 Counterfactual evaluation": (2, "Counterfactual Evaluation"),
    "2.6 The gap this work addresses": (2, "Research Gap"),
    "3. Paper idea": (1, "Proposed Approach"),
    "3.1 The claim": (2, "Hypothesis"),
    "3.2 How we thought about testing it": (2, "Evaluation Design Principles"),
    "3.3 Research questions": (2, "Research Questions"),
    "3.4 What would falsify the claim": (2, "Falsification Criteria"),
    "3.5 Novelty, stated carefully": (2, "Scope of Contribution"),
    "4. Complete discussion and implementation": (1, "System Design and Methodology"),
    "4.1 Starting point: audit of the original application": (2, "Audit of the Baseline System"),
    "4.2 Engineering for reproducibility": (2, "Reproducibility Framework"),
    "4.3 Skill extraction and training": (2, "Skill Extraction and Model Training"),
    "4.4 Data": (2, "Datasets and Evaluation Pools"),
    "4.5 The eight matchers and our entity-level scorer": (2, "Matching Models"),
    "4.6 Counterfactual perturbations": (2, "Counterfactual Perturbation Design"),
    "4.7 Metrics and statistics": (2, "Evaluation Metrics and Statistical Analysis"),
    "4.8 Main results": (2, "Main Results"),
    "4.9 Ablations: what controls the leakage?": (2, "Ablation Study"),
    "4.10 Choosing the final method, and the held-out check": (2, "Model Selection and Held-Out Validation"),
    "4.11 The near-miss suggestion band": (2, "Near-Miss Suggestion Calibration"),
    "4.12 Human annotation tool and the web application": (2, "Annotation Protocol and System Deployment"),
    "4.13 Limitations and threats to validity": (2, "Limitations and Threats to Validity"),
    "5. Conclusion": (1, "Conclusion"),
    "Future work": (2, "Future Work"),
}
NEW_SECTION_BEFORE = {"4.8 Main results": "Results and Discussion"}
# report subsection 4.n -> its label in this paper
SEC = {**{str(n): f"IV-{chr(64 + n)}" for n in range(1, 8)}, **{str(n): f"V-{chr(64 + n - 7)}" for n in range(8, 14)}}
XREFS = [
    ("the ablation in 4.9", f"the ablation in Section {SEC['9']}"),
    ("ablation finding of 4.9", f"ablation finding of Section {SEC['9']}"),
    ("section 4.13 says so", f"Section {SEC['13']} says so"),
    ("result in section 4.9", f"result in Section {SEC['9']}"),
    ("Measured in 4.8 and 4.9", f"Measured in Sections {SEC['8']} and {SEC['9']}"),
    ("results in 4.8\u20134.11", f"results in Sections {SEC['8']} to {SEC['11']}"),
    ("the final method (4.10)", f"the final method (Section {SEC['10']})"),
    ("(section 4.5) and is discussed in 4.13", f"(Section {SEC['5']}) and is discussed in Section {SEC['13']}"),
    ("reproduced exactly (4.1)", f"reproduced exactly (Section {SEC['1']})"),
    ("and section 4.5 describes", f"and Section {SEC['5']} describes"),
    ("chosen in 4.10", f"chosen in Section {SEC['10']}"),
    ("This section follows that order.", "Sections IV and V follow that order."),
]
EQUATIONS = [
    r"""\begin{equation}
\mathrm{score}(r, j) = \sum_{i \in E_j} \frac{\mathrm{idf}(i)}{\sum_{k \in E_j} \mathrm{idf}(k)} \, \max_{m \in E_r} \cos(\mathbf{e}_i, \mathbf{e}_m)
\end{equation}
\begin{equation}
\mathrm{idf}(e) = \ln\frac{N + 1}{\mathrm{df}(e) + 1} + 1
\end{equation}""",
    r"""\begin{equation}
\mathrm{gap}(b, j) = \frac{\lvert s'(b, j) - s(b, j) \rvert}{\sigma_j}
\end{equation}
where $\sigma_j$ is the SD of the original scores in pool $j$.""",
]
SYMBOLS = {"\u2264": r"$\le$", "\u2265": r"$\ge$", "\u00b1": r"$\pm$", "\u00d7": r"$\times$",
           "\u2192": r"$\rightarrow$", "\u2194": r"$\leftrightarrow$", "\u2208": r"$\in$", "\u2212": r"$-$",
           "\u03c3": r"$\sigma$", "\u0394": r"$\Delta$", "\u2248": r"$\approx$", "\u2032": r"$'$",
           "\u2022": r"\textbullet{}", "\u2026": r"\ldots{}"}
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(s: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in s)


def path_text(s: str) -> str:
    """Monospace identifier that may break after / - _ . (safe inside tables)."""
    t = esc(s)
    t = re.sub(r"(/|-|\.|\\_)", r"\1\\allowbreak{}", t)
    return r"\texttt{" + t + "}"


def inline(text: str) -> str:
    text = text.replace("&#91;", "[")
    keep: list[str] = []

    def stash(v):
        keep.append(v)
        return f"\x00{len(keep) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: stash(path_text(re.sub(r"\\(.)", r"\1", m.group(1)))), text)
    text = re.sub(r"\bE\\_([jr])\b", lambda m: stash(f"$E_{m.group(1)}$"), text)
    text = re.sub(r"\\(.)", lambda m: stash(esc(m.group(1))), text)
    text = re.sub(r"\[\[(\w+)\]\]", lambda m: stash(f"\\cite{{{m.group(1)}}}"), text)
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", text)
    text = re.sub(r'"([^"]+)"', r"``\1''", text)
    text = "".join(SYMBOLS.get(c, c) for c in text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], text)
    text = re.sub(r"\\cite\{(\w+)\}(?:, \\cite\{(\w+)\})+", lambda m: r"\cite{" + ",".join(re.findall(r"\\cite\{(\w+)\}", m.group(0))) + "}", text)
    return text


def ref_tex(s: str) -> str:
    """The IEEE reference strings in build_ieee.REFS are HTML; convert to LaTeX."""
    s = re.sub(r'<span class="tt">(.+?)</span>', lambda m: "\x00" + m.group(1) + "\x00", s)
    parts = re.split(r"(\x00[^\x00]*\x00)", s)
    out = []
    for p in parts:
        if p.startswith("\x00"):
            out.append(path_text(p.strip("\x00")))
        else:
            p = p.replace("&amp;", "&")
            p = re.sub(r"<i>(.+?)</i>", "\x01\\1\x02", p)
            p = esc(p)
            p = re.sub(r'"([^"]+)"', r"``\1''", p)
            out.append(p.replace("\x01", r"\emph{").replace("\x02", "}"))
    return "".join(out)


def colspec(head, data, total: str) -> tuple[str, str]:
    """Numeric columns centred, text columns flexible (tabularx X); returns (env, spec)."""
    numeric = [all(base.is_num(re.sub(r"\*\*", "", r[c])) for r in data) for c in range(len(head))]
    longest = [max(len(re.sub(r"[*`]", "", x)) for x in [head[c]] + [r[c] for r in data]) for c in range(len(head))]
    text_cols = [c for c in range(len(head)) if not numeric[c] and longest[c] > 22]
    # numeric columns whose header is much wider than their numbers get a wrapping header
    wrap_num = [c for c in range(len(head)) if numeric[c] and len(head[c]) > 8]
    if not text_cols and not wrap_num:
        return "tabular", "".join("c" if numeric[c] else "l" for c in range(len(head)))

    def col(c):
        if c in wrap_num:
            return ">{\\centering\\arraybackslash}X"
        if numeric[c]:
            return "c"
        return ">{\\raggedright\\arraybackslash}X" if c in text_cols else "l"

    return "tabularx", "".join(col(c) for c in range(len(head)))


def build_tex() -> str:
    md = (HERE / "report.md").read_text(encoding="utf-8")
    body, _, _ = md.partition("\n## References")
    for a, b in XREFS:
        assert a in body, a
        body = body.replace(a, b)
    body = re.sub(r"\| 4\.(\d+) \|", lambda m: f"| Section {SEC[m.group(1)]} |", body)
    body = base.cite(body)
    order: list[str] = []
    for k in re.findall(r"\[\[(\w+)\]\]", body):
        if k not in order:
            order.append(k)
    order += [k for k in base.REFS if k not in order]

    lines = body.split("\n")
    out: list[str] = []
    i = fig = tab = eq = 0
    abstract = False
    first = True
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("# "):                     # title + old byline: replaced by \maketitle
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            continue
        if ln.startswith("## ") or ln.startswith("### "):
            head = ln.lstrip("#").strip()
            if abstract:
                out.append(r"\end{abstract}" if not out[-1].startswith(r"\end{IEEEkeywords}") else "")
                abstract = False
            if head == "Abstract":
                out.append(r"\begin{abstract}")
                abstract = True
            else:
                if head in NEW_SECTION_BEFORE:
                    out.append(f"\\section{{{NEW_SECTION_BEFORE[head]}}}")
                level, new = HEADINGS[head]
                out.append(("\\section" if level == 1 else "\\subsection") + "{" + inline(new) + "}")
            i += 1
            continue
        if ln.startswith("```"):
            i += 1
            while not lines[i].startswith("```"):
                i += 1
            out.append(EQUATIONS[eq])
            eq += 1
            i += 1
            continue
        if ln.startswith("&#91;image:"):
            f, wide = base.FIGURES[fig]
            fig += 1
            j = i + 1
            while not lines[j].strip():
                j += 1
            cap = re.sub(r"^\*Figure \d+\.\s*(.*)\*$", r"\1", lines[j].strip())
            env = "figure*" if wide else "figure"
            width = r"0.9\textwidth" if wide else r"\columnwidth"
            out.append(f"\\begin{{{env}}}[!t]\n\\centering\n\\includegraphics[width={width}]{{figs/{f}}}\n"
                       f"\\caption{{{inline(cap)}}}\n\\label{{fig:{fig}}}\n\\end{{{env}}}")
            i = j + 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            title, wide = base.TABLES[tab]
            tab += 1
            head, data = rows[0], rows[2:]
            env, spec = colspec(head, data, "")
            width = r"\textwidth" if wide else r"\columnwidth"
            begin = f"\\begin{{tabularx}}{{{width}}}{{{spec}}}" if env == "tabularx" else f"\\begin{{tabular}}{{{spec}}}"
            body_rows = " \\\\\n".join(" & ".join(inline(c) for c in r) for r in data)
            fenv = "table*" if wide else "table"
            out.append(f"\\begin{{{fenv}}}[!t]\n\\caption{{{esc(title)}}}\n\\label{{tab:{tab}}}\n\\centering\n\\footnotesize\n"
                       f"{begin}\n\\hline\n" + " & ".join(r"\textbf{" + inline(h) + "}" for h in head) +
                       f" \\\\\n\\hline\n{body_rows} \\\\\n\\hline\n\\end{{{env}}}\n\\end{{{fenv}}}")
            continue
        if re.match(r"^(- |\d+\. )", ln):
            ordered = not ln.startswith("- ")
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                i += 1
                while i < len(lines) and not lines[i].strip() and i + 1 < len(lines) and re.match(r"^(- |\d+\. )", lines[i + 1]):
                    i += 1
            envl = "enumerate" if ordered else "itemize"
            out.append(f"\\begin{{{envl}}}\n" + "\n".join(f"\\item {inline(x)}" for x in items) + f"\n\\end{{{envl}}}")
            continue
        if ln.startswith("> "):
            out.append(r"\begin{quote}\itshape " + inline(ln[2:]) + r"\end{quote}")
            i += 1
            continue
        if abstract:
            if ln.startswith("**Keywords:**"):
                out.append(r"\end{abstract}")
                out.append(r"\begin{IEEEkeywords}" + inline(ln[len("**Keywords:**"):].strip()) + r"\end{IEEEkeywords}")
                abstract = False
            else:
                out.append(inline(ln) + "\n")
            i += 1
            continue
        m = re.match(r"^\*\*(.+?)\*\*(.*)$", ln)
        if m:                                      # bold lead-in -> IEEE third-level run-in heading
            out.append(f"\\subsubsection{{{inline(m.group(1).rstrip('.:'))}}} {inline(m.group(2).strip())}\n")
        else:
            out.append(inline(ln) + "\n")
        i += 1
    assert (fig, tab, eq) == (len(base.FIGURES), len(base.TABLES), len(EQUATIONS)), (fig, tab, eq)
    bib = "\n".join(f"\\bibitem{{{k}}} {ref_tex(base.REFS[k])}" for k in order)
    first = first and True
    return PREAMBLE + "\n".join(x for x in out if x) + f"""

\\balance
\\begin{{thebibliography}}{{99}}
\\item[] \\emph{{These entries were written from memory and have not been checked against the published versions. Verify authors, venues and years before submission.}}
{bib}
\\end{{thebibliography}}

\\end{{document}}
"""


PREAMBLE = rf"""\documentclass[conference,a4paper]{{IEEEtran}}
\IEEEoverridecommandlockouts
\usepackage{{fontspec}}
\setmainfont{{Times New Roman}}
\setmonofont{{Courier New}}[Scale=0.85]
\usepackage{{amsmath,amssymb}}
\usepackage{{graphicx}}
\usepackage{{array,tabularx}}
\usepackage[hyphens]{{url}}
\usepackage{{cite}}
\usepackage{{xcolor}}
\usepackage{{balance}}
\renewcommand{{\tabularxcolumn}}[1]{{p{{#1}}}}
\setlength{{\tabcolsep}}{{3pt}}
\urlstyle{{tt}}
\sloppy

\begin{{document}}

\title{{{TITLE}}}
\author{{\IEEEauthorblockN{{{AUTHOR[0]}}}
\IEEEauthorblockA{{{AUTHOR[1]}}}}}

\maketitle

"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    figs = OUT_DIR / "figs"
    figs.mkdir(exist_ok=True)
    for f, _ in base.FIGURES:
        shutil.copy2(base.FIG_DIR / f, figs / f)
    tex = OUT_DIR / "paper.tex"
    tex.write_text(build_tex(), encoding="utf-8")
    r = subprocess.run([str(TECTONIC), "--keep-logs", "paper.tex"], cwd=OUT_DIR, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    print(r.stdout[-3000:], r.stderr[-6000:])
    if r.returncode != 0:
        raise SystemExit(f"tectonic failed ({r.returncode})")
    shutil.copy2(OUT_DIR / "paper.pdf", OUT_PDF)
    print("wrote", OUT_PDF)


if __name__ == "__main__":
    main()
