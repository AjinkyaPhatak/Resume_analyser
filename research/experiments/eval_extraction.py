"""Phase 1: span-level evaluation of skill extractors on SkillSpan.

    python -m research.experiments.eval_extraction --config configs/extraction.yaml [--subset N]

Writes:
  results/extraction/metrics.csv          every (extractor, split, group, view, mode) row
  results/extraction/run_meta.json        config + git hash + env
  results/extraction.md                   summary tables (extraction_subsetN.md with --subset)
  results/extraction_examples.md          gold vs predicted spans on a few dev sentences

An extractor that cannot be built (e.g. ESCO CSV not downloaded yet) is reported as
NOT RUN with the reason. It is never filled with placeholder numbers.
"""

from __future__ import annotations

import csv
import time

import numpy as np

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import make_rng
from research.data.skillspan import load_skillspan
from research.extraction.registry import build_extractor
from research.metrics.span_metrics import SpanEvaluator


def _subset(sentences, n, seed):
    if n is None or n >= len(sentences):
        return sentences
    idx = sorted(make_rng(seed).permutation(len(sentences))[:n])
    return [sentences[i] for i in idx]


def _fmt(x: float) -> str:
    return f"{x:.3f}"


def _lookup(rows, extractor, split, group, view, mode):
    for r in rows:
        if (r["extractor"], r["split"], r["group"], r["view"], r["mode"]) == (extractor, split, group, view, mode):
            return r
    return None


def write_markdown(path, rows, not_run, cfg, sizes, timings):
    names = list(dict.fromkeys(r["extractor"] for r in rows))
    splits = cfg["eval"]["splits"]
    lines = ["# Skill extraction on SkillSpan", ""]
    if cfg.get("subset"):
        lines += [f"**PRELIMINARY: --subset {cfg['subset']} sentences per split.**", ""]
    lines += [
        f"SkillSpan `{cfg['datasets']['skillspan']['hf_id']}` @ "
        f"`{cfg['datasets']['skillspan']['revision'][:7]}`; sentences evaluated: "
        + ", ".join(f"{s}={sizes[s]}" for s in splits)
        + ". Gold = union of skill and knowledge layers unless stated. Micro-averaged.",
        "Exact = identical token boundaries. Partial = overlap of at least 1 token, with P and R "
        "counted separately (lenient; see research/metrics/span_metrics.py).",
        "",
        "## All spans (skill ∪ knowledge)",
        "",
        "| Extractor | Split | Exact P | Exact R | Exact F1 | Partial P | Partial R | Partial F1 | #pred | #gold |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for n in names:
        for s in splits:
            e = _lookup(rows, n, s, "all", "all", "exact")
            p = _lookup(rows, n, s, "all", "all", "partial")
            lines.append(
                f"| {n} | {s} | {_fmt(e['precision'])} | {_fmt(e['recall'])} | **{_fmt(e['f1'])}** | "
                f"{_fmt(p['precision'])} | {_fmt(p['recall'])} | **{_fmt(p['f1'])}** | {e['n_pred']} | {e['n_gold']} |"
            )
    groups_by_seed: dict[str, list[str]] = {}
    for spec in cfg["extractors"]:
        if spec.get("seed_group") and spec["name"] in names:
            groups_by_seed.setdefault(spec["seed_group"], []).append(spec["name"])
    if groups_by_seed:
        lines += ["", "## Mean ± SD over training seeds (all spans, F1)", "",
                  "| Extractor | Seeds | Split | Exact F1 | Partial F1 |", "|---|---|---|---|---|"]
        for group, members in groups_by_seed.items():
            for s in splits:
                ex = np.array([_lookup(rows, m, s, "all", "all", "exact")["f1"] for m in members])
                pa = np.array([_lookup(rows, m, s, "all", "all", "partial")["f1"] for m in members])
                sd = (lambda a: a.std(ddof=1) if len(a) > 1 else float("nan"))
                lines.append(f"| {group} | {len(members)} | {s} | {ex.mean():.3f} ± {sd(ex):.3f} | "
                             f"{pa.mean():.3f} ± {sd(pa):.3f} |")
    lines += [
        "",
        "## Per gold layer (F1)",
        "",
        "Predicted `skill`/`verb_phrase` spans are scored against the skill layer, and "
        "`knowledge` spans against the knowledge layer.",
        "",
        "| Extractor | Split | Skill exact | Skill partial | Knowledge exact | Knowledge partial |",
        "|---|---|---|---|---|---|",
    ]
    for n in names:
        for s in splits:
            vals = [_lookup(rows, n, s, "all", v, m)["f1"] for v in ("skill", "knowledge") for m in ("exact", "partial")]
            lines.append(f"| {n} | {s} | " + " | ".join(_fmt(v) for v in vals) + " |")
    groups = sorted({r["group"] for r in rows} - {"all"})
    if groups:
        lines += ["", "## By source (all spans, F1 exact / partial)", "",
                  "| Extractor | Split | " + " | ".join(groups) + " |",
                  "|---|---|" + "---|" * len(groups)]
        for n in names:
            for s in splits:
                cells = []
                for g in groups:
                    e = _lookup(rows, n, s, g, "all", "exact")
                    p = _lookup(rows, n, s, g, "all", "partial")
                    cells.append(f"{_fmt(e['f1'])} / {_fmt(p['f1'])}" if e else "–")
                lines.append(f"| {n} | {s} | " + " | ".join(cells) + " |")
    if timings:
        lines += ["", "Wall-clock seconds (build / extract all splits): "
                  + "; ".join(f"{n}: {b:.1f} / {x:.1f}" for n, (b, x) in timings.items())]
    if not_run:
        lines += ["", "## Not run", ""]
        lines += [f"- **{n}**: {reason}" for n, reason in not_run.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_examples(path, sentences, preds_by_extractor):
    lines = ["# Extraction examples (dev split)", "",
             "Gold spans are shown as `[text]`; S = skill layer, K = knowledge layer.", ""]
    for i, sent in enumerate(sentences):
        toks = sent.tokens
        lines.append(f"## {i + 1}. ({sent.source}) {' '.join(toks)}")
        lines.append("")
        lines.append("- gold S: " + (", ".join(f"[{' '.join(toks[a:b])}]" for a, b in sent.skill) or "–"))
        lines.append("- gold K: " + (", ".join(f"[{' '.join(toks[a:b])}]" for a, b in sent.knowledge) or "–"))
        for name, preds in preds_by_extractor.items():
            spans = preds[i]
            lines.append(f"- {name}: " + (", ".join(f"[{' '.join(toks[s.start:s.end])}]/{s.label[0].upper()}" for s in spans) or "–"))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/extraction.yaml").parse_args(argv)
    cfg = setup_run(args)
    data = load_skillspan(cfg["datasets"]["skillspan"]["local_dir"], splits=tuple(cfg["eval"]["splits"]))
    data = {s: _subset(v, cfg.get("subset"), cfg["seed"]) for s, v in data.items()}
    sizes = {s: len(v) for s, v in data.items()}
    results_dir = repo_path(cfg["paths"]["results"])
    out_dir = results_dir / "extraction"
    bs = int(cfg["eval"]["batch_size"])

    rows, not_run, timings, example_preds, extra = [], {}, {}, {}, {}
    n_ex = int(cfg["eval"]["n_examples"])
    for spec in cfg["extractors"]:
        name = spec["name"]
        t0 = time.perf_counter()
        try:
            extractor = build_extractor(spec, cfg)
        except FileNotFoundError as e:
            not_run[name] = str(e)
            print(f"[NOT RUN] {name}: {e}")
            continue
        build_s = time.perf_counter() - t0
        if hasattr(extractor, "pattern_stats"):
            extra[name] = extractor.pattern_stats
        t1 = time.perf_counter()
        for split, sents in data.items():
            preds = extractor.extract_tokens_batch([s.tokens for s in sents], batch_size=bs)
            ev = SpanEvaluator()
            for sent, pred in zip(sents, preds):
                ev.add(pred, {"all": sent.all_spans, "skill": sent.skill, "knowledge": sent.knowledge}, group=sent.source)
            for r in ev.rows():
                rows.append({"extractor": name, "split": split, **r})
            if split == "dev":
                example_preds[name] = preds[:n_ex]
        timings[name] = (build_s, time.perf_counter() - t1)
        print(f"[done] {name}: build {build_s:.1f}s, extract {timings[name][1]:.1f}s")

    out_dir.mkdir(parents=True, exist_ok=True)
    if rows:
        with open(out_dir / "metrics.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    write_run_metadata(out_dir, cfg, extra={"sizes": sizes, "not_run": not_run, "esco_stats": extra,
                                             "timings_s": timings})
    md_name = f"extraction_subset{cfg['subset']}.md" if cfg.get("subset") else "extraction.md"
    write_markdown(results_dir / md_name, rows, not_run, cfg, sizes, timings)
    if "dev" in data and example_preds:
        write_examples(results_dir / "extraction_examples.md", data["dev"][:n_ex], example_preds)
    print(f"wrote {results_dir / md_name}")


if __name__ == "__main__":
    main()
