"""Typeset report/report.md in the IEEE conference layout and print it to PDF.

    venv/Scripts/python.exe report/build_ieee.py

report.md is the Markdown export of the project report. This script changes FORMAT only:
A4, IEEE margins (19 mm top, 43 mm bottom, 14.32 mm sides), two columns with a 4.22 mm
gutter, Times New Roman 10 pt body, 24 pt title, 9 pt bold abstract, Roman-numbered
small-caps section heads, lettered italic subsection heads, "Fig. n." captions below
figures, "TABLE N" small-caps captions above tables, numbered references in order of first
citation. No LaTeX is installed here, so the page is HTML/CSS printed by headless Chrome;
it follows the IEEE template's measurements but is not compiled with IEEEtran.cls.
Output: Project_Report_IEEE.pdf in the repo root (and report/report_ieee.html).
"""

from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG_DIR = ROOT / "research" / "results" / "summaries" / "figures"
OUT_PDF = ROOT / "Project_Report_IEEE.pdf"
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]

AUTHOR = ("Ajinkya Phatak", "Registration No. 23BCE0643")
FIGURES = [  # in document order: file, spans both columns?
    ("report_pipeline.png", True), ("report_extraction_f1.png", False), ("report_training_curves.png", True),
    ("headline_accuracy_vs_gap.png", False), ("perturbation_gaps.png", True), ("report_selection_dev.png", False),
    ("report_heldout.png", False), ("nearmiss_heatmap_dev.png", False), ("nearmiss_curves.png", True),
]
TABLES = [  # in document order: IEEE title, spans both columns?
    ("Research Questions", False), ("Project Phases", True), ("Ground Rules and Their Implementation", True),
    ("Skill Extractors", True), ("Extraction Results on the SkillSpan Test Set", False),
    ("Fine-Tuning Settings", False), ("Fine-Tuned Tagger Results by Seed", False),
    ("BiasBios Splits After Cleaning", False), ("Matchers Compared", True), ("Counterfactual Conditions", True),
    ("Perturbation Coverage on Test Bios", False), ("Example Counterfactuals From the Dev Split", True),
    ("Ranking Accuracy on 234 Test Pools", False),
    ("Counterfactual Gap by Condition (Pool SDs, Changed Bios)", True),
    ("Paired Tests Against Each Baseline, Full Gender Flip", False), ("Group Fairness Metrics", True),
    ("Ablation: Extractor", True), ("Ablation: Entity Types", True), ("Ablation: Entity Encoder", False),
    ("Ablation: Aggregation", False), ("Held-Out Check on 34 Untouched Test Pools", True),
    ("Suggestion Precision by Band", False), ("Limitations and Mitigations", True),
]
# (first author surname, year) -> reference key
CITES = {
    ("Robertson", "2009"): "bm25", ("Reimers", "2019"): "sbert", ("Wang", "2020"): "minilm",
    ("Song", "2020"): "mpnet", ("Nogueira", "2019"): "monobert", ("Khattab", "2020"): "colbert",
    ("Zhang", "2020"): "bertscore", ("Zhu", "2018"): "pjfnn", ("Qin", "2018"): "apjfnn",
    ("Zhang", "2022"): "skillspan", ("Decorte", "2021"): "jobbert", ("Bertrand", "2004"): "bertrand",
    ("Gaucher", "2011"): "gaucher", ("Madera", "2009"): "madera", ("Bolukbasi", "2016"): "bolukbasi",
    ("De-Arteaga", "2019"): "biasbios", ("Dastin", "2018"): "dastin", ("Raghavan", "2020"): "raghavan",
    ("Wilson", "2024"): "wilson", ("Kusner", "2017"): "kusner", ("Lu", "2018"): "lu", ("Zhao", "2018"): "zhao",
    ("Garg", "2019"): "garg", ("Hardt", "2016"): "hardt", ("Singh", "2018"): "singh",
    ("McSherry", "2008"): "mcsherry",
}
REFS = {  # IEEE reference style; written from memory, as the report itself states
    "bm25": 'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," <i>Found. Trends Inf. Retr.</i>, 2009.',
    "sbert": 'N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in <i>Proc. EMNLP</i>, 2019.',
    "minilm": 'W. Wang <i>et al.</i>, "MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers," in <i>Proc. NeurIPS</i>, 2020.',
    "mpnet": 'K. Song <i>et al.</i>, "MPNet: Masked and permuted pre-training for language understanding," in <i>Proc. NeurIPS</i>, 2020.',
    "monobert": 'R. Nogueira and K. Cho, "Passage re-ranking with BERT," <i>arXiv</i> preprint, 2019.',
    "colbert": 'O. Khattab and M. Zaharia, "ColBERT: Efficient and effective passage search via contextualized late interaction over BERT," in <i>Proc. SIGIR</i>, 2020.',
    "bertscore": 'T. Zhang, V. Kishore, F. Wu, K. Weinberger, and Y. Artzi, "BERTScore: Evaluating text generation with BERT," in <i>Proc. ICLR</i>, 2020.',
    "pjfnn": 'C. Zhu <i>et al.</i>, "Person-job fit: Adapting the right talent for the right job with joint representation learning," <i>ACM Trans. Manage. Inf. Syst.</i>, 2018.',
    "apjfnn": 'C. Qin <i>et al.</i>, "Enhancing person-job fit for talent recruitment: An ability-aware neural network approach," in <i>Proc. SIGIR</i>, 2018.',
    "skillspan": 'M. Zhang, K. N. Jensen, S. D. Sonniks, and B. Plank, "SkillSpan: Hard and soft skill extraction from English job postings," in <i>Proc. NAACL</i>, 2022.',
    "jobbert": 'J.-J. Decorte, J. Van Hautte, T. Demeester, and C. Develder, "JobBERT: Understanding job titles through skills," in <i>FEAST Workshop, ECML-PKDD</i>, 2021.',
    "bertrand": 'M. Bertrand and S. Mullainathan, "Are Emily and Greg more employable than Lakisha and Jamal? A field experiment on labor market discrimination," <i>Amer. Econ. Rev.</i>, 2004.',
    "gaucher": 'D. Gaucher, J. Friesen, and A. C. Kay, "Evidence that gendered wording in job advertisements exists and sustains gender inequality," <i>J. Pers. Soc. Psychol.</i>, 2011.',
    "madera": 'J. M. Madera, M. R. Hebl, and R. C. Martin, "Gender and letters of recommendation for academia: Agentic and communal differences," <i>J. Appl. Psychol.</i>, 2009.',
    "bolukbasi": 'T. Bolukbasi <i>et al.</i>, "Man is to computer programmer as woman is to homemaker? Debiasing word embeddings," in <i>Proc. NeurIPS</i>, 2016.',
    "biasbios": 'M. De-Arteaga <i>et al.</i>, "Bias in bios: A case study of semantic representation bias in a high-stakes setting," in <i>Proc. FAT*</i>, 2019.',
    "dastin": 'J. Dastin, "Amazon scraps secret AI recruiting tool that showed bias against women," <i>Reuters</i>, 2018.',
    "raghavan": 'M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, "Mitigating bias in algorithmic hiring: Evaluating claims and practices," in <i>Proc. FAT*</i>, 2020.',
    "wilson": 'K. Wilson and A. Caliskan, "Gender, race, and intersectional bias in resume screening via language model retrieval," in <i>Proc. AIES</i>, 2024.',
    "kusner": 'M. Kusner, J. Loftus, C. Russell, and R. Silva, "Counterfactual fairness," in <i>Proc. NeurIPS</i>, 2017.',
    "lu": 'K. Lu, P. Mardziel, F. Wu, P. Amancharla, and A. Datta, "Gender bias in neural natural language processing," <i>arXiv</i> preprint, 2018.',
    "zhao": 'J. Zhao, T. Wang, M. Yatskar, V. Ordonez, and K.-W. Chang, "Gender bias in coreference resolution: Evaluation and debiasing methods," in <i>Proc. NAACL</i>, 2018.',
    "garg": 'S. Garg <i>et al.</i>, "Counterfactual fairness in text classification through robustness," in <i>Proc. AIES</i>, 2019.',
    "hardt": 'M. Hardt, E. Price, and N. Srebro, "Equality of opportunity in supervised learning," in <i>Proc. NeurIPS</i>, 2016.',
    "singh": 'A. Singh and T. Joachims, "Fairness of exposure in rankings," in <i>Proc. KDD</i>, 2018.',
    "mcsherry": 'F. McSherry and M. Najork, "Computing information retrieval performance measures efficiently in the presence of tied scores," in <i>Proc. ECIR</i>, 2008.',
    # listed in the report's reference list but not cited in running text
    "jobbertv2": 'TechWolf, "JobBERT-v2," model card, Hugging Face (<span class="tt">TechWolf/JobBERT-v2</span>).',
    "esco": 'European Commission, "ESCO: European Skills, Competences, Qualifications and Occupations," v1.2.1.',
    "ndcg": 'K. J\u00e4rvelin and J. Kek\u00e4l\u00e4inen, "Cumulated gain-based evaluation of IR techniques," <i>ACM Trans. Inf. Syst.</i>, 2002.',
    "bootstrap": 'B. Efron and R. Tibshirani, <i>An Introduction to the Bootstrap</i>. Chapman &amp; Hall, 1993.',
    "holm": 'S. Holm, "A simple sequentially rejective multiple test procedure," <i>Scand. J. Statist.</i>, 1979.',
    "cohen": 'J. Cohen, "A coefficient of agreement for nominal scales," <i>Educ. Psychol. Meas.</i>, 1960.',
    "krippendorff": 'K. Krippendorff, <i>Content Analysis: An Introduction to Its Methodology</i>. Sage, 2004.',
    "d_biasbios": 'BiasBios dataset, <span class="tt">LabHC/bias_in_bios</span>, Hugging Face (MIT licence).',
    "d_linkedin": 'LinkedIn Job Postings dataset, <span class="tt">arshkon/linkedin-job-postings</span>, Kaggle (CC BY-SA 4.0).',
    "d_ssa": 'U.S. Social Security Administration, national baby-name counts (via the Hugging Face mirror <span class="tt">nkrishnaswami/us-ssa-baby-names-national</span>).',
    "d_wikidata": 'Wikidata, given names of people with Indian citizenship (CC0); query archived in the project repository.',
}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
SEC4 = {str(i + 1): "IV-" + chr(ord("A") + i) for i in range(13)}
XREFS = [  # cross-references renumbered for IEEE section labels
    ("the ablation in 4.9", "the ablation in Section IV-I"), ("ablation finding of 4.9", "ablation finding of Section IV-I"),
    ("section 4.13 says so", "Section IV-M says so"), ("result in section 4.9", "result in Section IV-I"),
    ("Measured in 4.8 and 4.9", "Measured in Sections IV-H and IV-I"),
    ("results in 4.8\u20134.11", "results in Sections IV-H to IV-K"), ("the final method (4.10)", "the final method (Section IV-J)"),
    ("(section 4.5) and is discussed in 4.13", "(Section IV-E) and is discussed in Section IV-M"),
    ("reproduced exactly (4.1)", "reproduced exactly (Section IV-A)"), ("and section 4.5 describes", "and Section IV-E describes"),
    ("chosen in 4.10", "chosen in Section IV-J"),
]
EQUATIONS = [  # the report's two display formulas, as MathML (numbered as IEEE requires)
    """<div class="eq"><math display="block"><mrow><mtext>score</mtext><mo stretchy="false">(</mo><mi>r</mi><mo>,</mo><mi>j</mi><mo stretchy="false">)</mo><mo>=</mo>
<munder><mo>&#x2211;</mo><mrow><mi>i</mi><mo>&#x2208;</mo><msub><mi>E</mi><mi>j</mi></msub></mrow></munder>
<mfrac><mrow><mi>idf</mi><mo stretchy="false">(</mo><mi>i</mi><mo stretchy="false">)</mo></mrow><mrow><munder><mo>&#x2211;</mo><mrow><mi>k</mi><mo>&#x2208;</mo><msub><mi>E</mi><mi>j</mi></msub></mrow></munder><mi>idf</mi><mo stretchy="false">(</mo><mi>k</mi><mo stretchy="false">)</mo></mrow></mfrac>
<munder><mi>max</mi><mrow><mi>m</mi><mo>&#x2208;</mo><msub><mi>E</mi><mi>r</mi></msub></mrow></munder>
<mi>cos</mi><mo stretchy="false">(</mo><msub><mi mathvariant="bold">e</mi><mi>i</mi></msub><mo>,</mo><msub><mi mathvariant="bold">e</mi><mi>m</mi></msub><mo stretchy="false">)</mo></mrow></math><span class="eqno">(1)</span></div>
<div class="eq"><math display="block"><mrow><mi>idf</mi><mo stretchy="false">(</mo><mi>e</mi><mo stretchy="false">)</mo><mo>=</mo><mi>ln</mi>
<mfrac><mrow><mi>N</mi><mo>+</mo><mn>1</mn></mrow><mrow><mi>df</mi><mo stretchy="false">(</mo><mi>e</mi><mo stretchy="false">)</mo><mo>+</mo><mn>1</mn></mrow></mfrac><mo>+</mo><mn>1</mn></mrow></math><span class="eqno">(2)</span></div>""",
    """<div class="eq"><math display="block"><mrow><mtext>gap</mtext><mo stretchy="false">(</mo><mi>b</mi><mo>,</mo><mi>j</mi><mo stretchy="false">)</mo><mo>=</mo>
<mfrac><mrow><mo stretchy="false">|</mo><msup><mi>s</mi><mo>&#x2032;</mo></msup><mo stretchy="false">(</mo><mi>b</mi><mo>,</mo><mi>j</mi><mo stretchy="false">)</mo><mo>&#x2212;</mo><mi>s</mi><mo stretchy="false">(</mo><mi>b</mi><mo>,</mo><mi>j</mi><mo stretchy="false">)</mo><mo stretchy="false">|</mo></mrow><msub><mi>&#x3C3;</mi><mi>j</mi></msub></mfrac></mrow></math><span class="eqno">(3)</span></div>
<p class="noindent">where <i>&#x3C3;<sub>j</sub></i> is the SD of the original scores in pool <i>j</i>.</p>""",
]

CSS = """
@page { size: A4; margin: 19mm 14.32mm 43mm 14.32mm; }
* { box-sizing: border-box; }
html { font-family: "Times New Roman", Times, serif; font-size: 10pt; line-height: 12pt; color: #000; }
body { margin: 0; columns: 2; column-gap: 4.22mm; column-fill: balance; text-align: justify; hyphens: auto;
       orphans: 2; widows: 2; }
.front { column-span: all; text-align: center; margin-bottom: 12pt; }
.front h1 { font-size: 24pt; line-height: 28pt; font-weight: normal; margin: 0 0 10pt; hyphens: none; }
.front .author { font-size: 11pt; line-height: 13pt; }
.front .affil { font-size: 10pt; line-height: 12pt; font-style: italic; }
p { margin: 0; text-indent: 1pc; }
p.noindent { text-indent: 0; }
.abstract p { font-size: 9pt; line-height: 10.5pt; font-weight: bold; }
.abstract { margin-bottom: 9pt; }
h2 { font-size: 10pt; font-weight: normal; font-variant: small-caps; text-align: center; margin: 9pt 0 4pt;
     letter-spacing: .02em; break-after: avoid; hyphens: none; }
h3 { font-size: 10pt; font-weight: normal; font-style: italic; text-align: left; margin: 7pt 0 3pt;
     break-after: avoid; hyphens: none; }
.runin { font-style: italic; }
ul, ol { margin: 2pt 0 2pt 0; padding-left: 1.6pc; }
li { margin: 0; }
blockquote { margin: 3pt 1pc; font-style: italic; }
blockquote p { text-indent: 0; }
code, .tt { font-family: "Courier New", Courier, monospace; font-size: 8.5pt; hyphens: none; word-break: break-word; }
figure { margin: 8pt 0; text-align: center; break-inside: avoid; }
figure.wide, .tablewrap.wide { column-span: all; }
figure img { max-width: 100%; }
figure.wide img { max-width: 86%; }
figcaption { font-size: 8pt; line-height: 9.5pt; text-align: justify; margin-top: 4pt; hyphens: auto; }
.tablewrap { margin: 8pt 0; break-inside: avoid; }
.tcap { font-size: 8pt; line-height: 10pt; text-align: center; margin-bottom: 3pt; hyphens: none; }
.tcap .tnum { display: block; }
.tcap .ttitle { font-variant: small-caps; }
table { border-collapse: collapse; margin: 0 auto; font-size: 8pt; line-height: 9.5pt; text-align: left; hyphens: none;
        border-top: .8pt solid #000; border-bottom: .8pt solid #000; max-width: 100%; }
th { font-weight: bold; border-bottom: .5pt solid #000; padding: 2pt 4pt; vertical-align: bottom; }
td { padding: 1.5pt 4pt; vertical-align: top; }
td.num, th.num { text-align: center; white-space: nowrap; }
.eq { display: flex; align-items: center; margin: 5pt 0; }
.eq math { flex: 1; font-size: 9.5pt; }
.eqno { width: 2em; text-align: right; }
.refs { font-size: 8pt; line-height: 9.5pt; }
.refs p { text-indent: 0; }
.ref { display: flex; text-align: justify; }
.ref .n { flex: 0 0 2.2em; }
.refnote { font-style: italic; margin-bottom: 3pt; }
.refs .tt { font-size: 7pt; }
table code { font-size: 7pt; }
"""


def inline(text: str) -> str:
    """Markdown inline -> HTML (escapes, code, bold, italic)."""
    text = text.replace("&#91;", "[")
    codes: list[str] = []

    def stash(m):
        codes.append("<code>" + html.escape(re.sub(r"\\(.)", r"\1", m.group(1))) + "</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    esc: list[str] = []

    def keep(m):
        esc.append(html.escape(m.group(1)))
        return f"\x01{len(esc) - 1}\x01"

    text = re.sub(r"\\(.)", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"\bE\x01\d+\x01([jr])\b", r"<i>E</i><sub><i>\1</i></sub>", text)      # E\_j, E\_r in running text
    text = re.sub(r"\x01(\d+)\x01", lambda m: esc[int(m.group(1))], text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)
    return text


def cite(md: str) -> str:
    """Author-year citations -> [[key]] placeholders."""
    def paren(m):
        keys = []
        for piece in m.group(1).split(";"):
            pm = re.match(r"\s*([A-Z][\w-]+).*?,\s*((?:19|20)\d\d)\s*$", piece)
            key = CITES.get((pm.group(1), pm.group(2))) if pm else None
            if key is None:
                return m.group(0)
            keys.append(f"[[{key}]]")
        return ", ".join(keys)

    md = re.sub(r"\(([^()]*?(?:19|20)\d\d)\)", paren, md)

    def narrative(m):
        key = CITES.get((m.group(1), m.group(3)))
        if key is None:
            return m.group(0)
        return f"{m.group(1)}{m.group(2).replace(' & ', ' and ')} [[{key}]]"

    return re.sub(r"([A-Z][\w-]+)((?:,? [A-Z][\w-]+)*(?: & [A-Z][\w-]+| et al\.)?) \(((?:19|20)\d\d)\)", narrative, md)


def is_num(cell: str) -> bool:
    return bool(re.fullmatch(r"[<\u2264\u2265]?\s*[+\u2212-]?[\d.,]+%?(\s*\u00b1\s*[\d.]+)?(\s*\[[^\]]*\])?(\s*/\s*[\d.]+)?", cell.strip()))


def build() -> str:
    md = (HERE / "report.md").read_text(encoding="utf-8")
    body, _, _ = md.partition("\n## References")
    for a, b in XREFS:
        assert a in body, a
        body = body.replace(a, b)
    body = re.sub(r"\| 4\.(\d+) \|", lambda m: f"| Section {SEC4[m.group(1)]} |", body)
    body = cite(body)
    order: list[str] = []
    for k in re.findall(r"\[\[(\w+)\]\]", body):
        if k not in order:
            order.append(k)
    order += [k for k in REFS if k not in order]
    body = re.sub(r"\[\[(\w+)\]\]", lambda m: f"[{order.index(m.group(1)) + 1}]", body)

    lines = body.split("\n")
    out: list[str] = []
    i, sec, sub, run, fig, tab, eq = 0, 0, 0, 0, 0, 0, 0
    in_abstract = False
    title = ""
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("# "):
            title = ln[2:].strip()
            i += 2 if i + 1 < len(lines) else 1
            while i < len(lines) and not lines[i].startswith("## "):      # skip the old byline
                i += 1
            out.append(f'<div class="front"><h1>{inline(title)}</h1><div class="author">{AUTHOR[0]}</div>'
                       f'<div class="affil">{AUTHOR[1]}</div></div>')
            continue
        if ln.startswith("## "):
            head = ln[3:].strip()
            if in_abstract:
                out.append("</div>")
                in_abstract = False
            if head == "Abstract":
                in_abstract, first_abs = True, True
                out.append('<div class="abstract">')
            else:
                head = re.sub(r"^\d+\.\s*", "", head)
                sec, sub, run = sec + 1, 0, 0
                out.append(f"<h2>{ROMAN[sec - 1]}. {inline(head)}</h2>")
            i += 1
            continue
        if ln.startswith("### "):
            head = re.sub(r"^\d+\.\d+\s*", "", ln[4:].strip())
            sub, run = sub + 1, 0
            out.append(f"<h3>{chr(ord('A') + sub - 1)}. {inline(head)}</h3>")
            i += 1
            continue
        if ln.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append(EQUATIONS[eq])
            eq += 1
            i = j + 1
            continue
        if ln.startswith("&#91;image:"):
            f, wide = FIGURES[fig]
            fig += 1
            j = i + 1
            while not lines[j].strip():
                j += 1
            cap = re.sub(r"^\*Figure \d+\.\s*(.*)\*$", r"\1", lines[j].strip())
            assert cap != lines[j].strip(), lines[j]
            out.append(f'<figure class="{"wide" if wide else ""}"><img src="{(FIG_DIR / f).as_uri()}" alt="">'
                       f"<figcaption>Fig. {fig}.&nbsp; {inline(cap)}</figcaption></figure>")
            i = j + 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            ttitle, wide = TABLES[tab]
            tab += 1
            head, data = rows[0], rows[2:]
            numcol = [all(is_num(re.sub(r"\*\*", "", r[c])) for r in data) for c in range(len(head))]
            th = "".join(f'<th class="{"num" if numcol[c] else ""}">{inline(h)}</th>' for c, h in enumerate(head))
            trs = "".join("<tr>" + "".join(f'<td class="{"num" if numcol[c] else ""}">{inline(v)}</td>'
                                           for c, v in enumerate(r)) + "</tr>" for r in data)
            out.append(f'<div class="tablewrap {"wide" if wide else ""}"><div class="tcap"><span class="tnum">TABLE '
                       f'{roman(tab)}</span><span class="ttitle">{html.escape(ttitle)}</span></div>'
                       f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>")
            continue
        if re.match(r"^(- |\d+\. )", ln):
            ordered = not ln.startswith("- ")
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                i += 1
                while i < len(lines) and not lines[i].strip() and i + 1 < len(lines) and re.match(r"^(- |\d+\. )", lines[i + 1]):
                    i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if ln.startswith("> "):
            out.append(f"<blockquote><p>{inline(ln[2:])}</p></blockquote>")
            i += 1
            continue
        # paragraph
        if in_abstract:
            if ln.startswith("**Keywords:**"):
                out.append(f'<p class="noindent" style="margin-top:4pt"><i>Index Terms</i>&mdash;{inline(ln[len("**Keywords:**"):].strip())}</p>')
            else:
                out.append(f'<p class="{"noindent" if first_abs else ""}">{"<i>Abstract</i>&mdash;" if first_abs else ""}{inline(ln)}</p>')
                first_abs = False
            i += 1
            continue
        m = re.match(r"^\*\*(.+?)\*\*(.*)$", ln)
        if m:                                    # bold lead-in -> IEEE third-level run-in head
            run += 1
            head = m.group(1).rstrip(".:")
            rest = m.group(2).strip()
            out.append(f'<p><span class="runin">{run}) {inline(head)}:</span> {inline(rest)}</p>')
        else:
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    assert (fig, tab, eq) == (len(FIGURES), len(TABLES), len(EQUATIONS)), (fig, tab, eq)
    if in_abstract:
        out.append("</div>")
    out.append("<h2>References</h2>")
    out.append('<div class="refs"><p class="refnote">These entries were written from memory and have not been checked '
               "against the published versions. Verify authors, venues and years before submission.</p>")
    out += [f'<div class="ref"><span class="n">[{n}]</span><span>{REFS[k]}</span></div>' for n, k in enumerate(order, 1)]
    out.append("</div>")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f"<style>{CSS}</style></head><body>{''.join(out)}</body></html>")


def roman(n: int) -> str:
    out = ""
    for v, s in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out, n = out + s, n - v
    return out


def main():
    page = HERE / "report_ieee.html"
    page.write_text(build(), encoding="utf-8")
    chrome = next(c for c in CHROME if Path(c).is_file())
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT_PDF}", page.as_uri()], check=True, capture_output=True, timeout=180)
    print("wrote", OUT_PDF, OUT_PDF.stat().st_size)


if __name__ == "__main__":
    main()
