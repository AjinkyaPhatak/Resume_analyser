"""Dev-split error analysis for an extractor (never run on test: this informs tuning).

    python -m research.experiments.extraction_errors --set analyse=esco [--subset N]

Writes results/extraction_errors_<name>.md with:
  * the most frequent false-positive surface forms (predicted, overlapping no gold span);
  * the most frequent exact-match misses where a prediction overlaps the gold span
    (boundary errors), and gold spans with no overlapping prediction at all;
  * how many predictions fall in sentences with no gold annotation at all.
"""

from __future__ import annotations

import collections

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.data.skillspan import load_skillspan
from research.extraction.registry import build_extractor


def _ov(a, b):
    return a[0] < b[1] and b[0] < a[1]


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/extraction.yaml").parse_args(argv)
    cfg = setup_run(args)
    name = cfg.get("analyse", "esco")
    spec = next(s for s in cfg["extractors"] if s["name"] == name)
    dev = load_skillspan(cfg["datasets"]["skillspan"]["local_dir"], splits=("dev",))["dev"]
    if cfg.get("subset"):
        dev = dev[: cfg["subset"]]
    ex = build_extractor(spec, cfg)
    preds = ex.extract_tokens_batch([s.tokens for s in dev])

    fp, boundary, missed = collections.Counter(), collections.Counter(), collections.Counter()
    fp_by_source = collections.Counter()
    n_pred = n_pred_unannotated = 0
    for sent, spans in zip(dev, preds):
        gold = sent.all_spans
        toks = sent.tokens
        n_pred += len(spans)
        if not gold:
            n_pred_unannotated += len(spans)
        for s in spans:
            if not any(_ov((s.start, s.end), g) for g in gold):
                fp[" ".join(toks[s.start:s.end]).lower()] += 1
                fp_by_source[s.source] += 1
        pb = {(s.start, s.end) for s in spans}
        for g in gold:
            if g in pb:
                continue
            gtext = " ".join(toks[g[0]:g[1]])
            hits = [p for p in pb if _ov(p, g)]
            if hits:
                ptxt = " | ".join(" ".join(toks[a:b]) for a, b in sorted(hits))
                boundary[f"{gtext}  ⟶  {ptxt}"] += 1
            else:
                missed[gtext.lower()] += 1

    out = repo_path(cfg["paths"]["results"]) / f"extraction_errors_{name}.md"
    lines = [f"# Error analysis: {name} (SkillSpan dev, {len(dev)} sentences)", "",
             f"- predictions: {n_pred}; in sentences with no gold span at all: {n_pred_unannotated} "
             f"({n_pred_unannotated / max(n_pred, 1):.1%})",
             f"- false positives by source: {dict(fp_by_source)}", "",
             "## Top false-positive strings (no overlap with any gold span)", "",
             "| count | text |", "|---|---|"]
    lines += [f"| {c} | {t} |" for t, c in fp.most_common(60)]
    lines += ["", "## Boundary errors (gold ⟶ overlapping predictions), top 40", "", "| count | gold ⟶ pred |", "|---|---|"]
    lines += [f"| {c} | {t} |" for t, c in boundary.most_common(40)]
    lines += ["", f"Total boundary-error gold spans: {sum(boundary.values())}", "",
              "## Gold spans with no overlapping prediction, top 40", "", "| count | gold |", "|---|---|"]
    lines += [f"| {c} | {t} |" for t, c in missed.most_common(40)]
    lines += ["", f"Total fully-missed gold spans: {sum(missed.values())}"]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
