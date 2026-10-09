"""The paper's final matcher, served to the web app.

The app runs the exact research code (``research/``), not a re-implementation:
  * scoring = ``entity_li`` from research/configs/scorers.yaml: skill/knowledge entities
    from union(fine-tuned JobBERT tagger, ESCO EntityRuler, filtered noun chunks),
    JobBERT-v2 entity embeddings, IDF-weighted MaxSim (late interaction, cf. ColBERT /
    BERTScore; the mechanism is not ours, the fairness audit is);
  * suggestions = the near-miss band chosen on DEV in Phase 6 (ESCO entities, MiniLM);
  * counterfactual check = the paper's perturbation conditions, scored by entity_li and
    two comparison scorers (full-text MiniLM, and the app's old matcher).
Fitted statistics (IDF table, dev calibration, pool SDs, the band) come from
backend/artifacts/entity_li.json, written by ``python -m research.analysis.export_app``.
User texts are never written to disk: the research caches are switched off here.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import threading
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = Path(__file__).resolve().parents[2] / "artifacts" / "entity_li.json"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# shown when a condition has no counterpart in the paper's tables
CONDITION_LABELS = {
    "pronoun_swap": "Pronouns swapped (she ↔ he, her ↔ his/him, Ms ↔ Mr)",
    "name_swap_us": "First name swapped to a US name of the other gender",
    "name_swap_in": "First name swapped to an Indian name of the other gender",
    "name_in_same_gender": "First name swapped to an Indian name of the same gender",
    "affiliation_swap": "Gendered affiliations swapped (e.g. women's college ↔ men's)",
    "agentic_communal": "Agentic wording rewritten as communal (led → supported, …)",
    "gender_full": "Full gender flip (pronouns + first name)",
}
SOURCE_LABELS = {"model": "JobBERT tagger", "esco": "ESCO taxonomy", "noun_chunk": "noun phrase"}


_BULLET = re.compile(r"^[\s\u2022\u25aa\u25cf\u2013\u2014*\-\u00b7]+")   # leading bullets/dashes


def layout_to_sentences(text: str) -> str:
    """End every layout line (header, bullet, heading) as its own sentence.

    Resumes and pasted postings are line-structured; without this, spaCy parses a header
    such as "Jane Doe / Data Engineer / Jane ..." (one item per line) as one noun chunk.
    The research texts (BiasBios bios, LinkedIn descriptions) contain no line breaks, so on
    them this is a no-op and the app scores exactly as the paper's method does.
    """
    if "\n" not in text:
        return text
    lines = []
    for raw in text.splitlines():
        line = _BULLET.sub("", raw).strip()
        if line:
            lines.append(line if line[-1] in ".!?:;," else line + ".")
    return "\n".join(lines)


class EngineUnavailable(RuntimeError):
    """Models or artifacts are missing; the message says how to create them."""


def _percentile(value: float, quantiles: list[float]) -> float:
    """Share (0-100) of the calibration distribution at or below ``value``."""
    q = np.asarray(quantiles, float)
    levels = np.linspace(0, 100, len(q))
    if value <= q[0]:
        return 0.0
    if value >= q[-1]:
        return 100.0
    # quantile functions can be flat (many tied scores); take the upper end of a flat run
    idx = int(np.searchsorted(q, value, side="right"))
    lo, hi = q[idx - 1], q[idx]
    frac = 0.0 if hi == lo else (value - lo) / (hi - lo)
    return float(levels[idx - 1] + frac * (levels[idx] - levels[idx - 1]))


class MatchEngine:
    def __init__(self, artifact_path: Path = ARTIFACT):
        if not artifact_path.is_file():
            raise EngineUnavailable(f"Missing {artifact_path}. Run: python -m research.analysis.export_app")
        self.art = json.loads(artifact_path.read_text(encoding="utf-8"))
        from research.common.config import load_config
        from research.scorers.registry import build_encoder, build_extractor_for_scoring, build_scorer

        cfg = load_config("configs/main.yaml")
        cfg["persist_cache"] = False
        cfg["backbones"] = self.art["method"]["backbones"]
        self.cfg = cfg
        try:
            self.scorer = build_scorer(self.art["method"]["scorer"], cfg)
            self.scorer.extractor.extract_batch(["warm-up"])          # loads the tagger + ESCO now
        except (FileNotFoundError, OSError) as e:
            raise EngineUnavailable(str(e)) from e
        self.scorer.idf = self.art["idf"]["table"]
        self.scorer.idf_unseen = self.art["idf"]["unseen"]
        nm = self.art["nearmiss"]
        self.esco = build_extractor_for_scoring(nm["extractor"], cfg)
        self.nm_encoder = build_encoder(cfg["backbones"][nm["backbone"]], cfg, self.scorer.encoder.device)
        self.compare = {s["name"]: build_scorer(s, cfg) for s in self.art["method"]["compare"]}
        self._perturb = None
        self.lock = threading.Lock()

    # --- matching --------------------------------------------------------------------------
    def _entities(self, spans) -> tuple[list[str], dict[str, list[str]]]:
        """Kept entity strings (as the scorer sees them) and the extractors that found each."""
        ents = self.scorer.entities(spans)
        found: dict[str, set[str]] = {}
        for s in spans:
            if self.scorer._keep(s):
                found.setdefault(self.scorer._key(s.text), set()).add(SOURCE_LABELS.get(s.source, s.source))
        return ents, {e: sorted(found.get(self.scorer._key(e), ())) for e in ents}

    def match(self, resume: str, jd: str) -> dict:
        resume, jd = layout_to_sentences(resume), layout_to_sentences(jd)
        with self.lock:
            r_spans, j_spans = self.scorer.extractor.extract_batch([resume, jd])
            r_ents, r_src = self._entities(r_spans)
            j_ents, j_src = self._entities(j_spans)
            if not j_ents:
                raise ValueError("No skills were found in the job description. Paste the full posting text.")
            requirements = []
            if r_ents:
                vec = dict(zip(r_ents + j_ents, self.scorer.encoder.encode(r_ents + j_ents)))
                sim = np.stack([vec[e] for e in j_ents]) @ np.stack([vec[e] for e in r_ents]).T
                best = sim.argmax(axis=1)
            idf = np.array([self.scorer.idf.get(self.scorer._key(e), self.scorer.idf_unseen) for e in j_ents])
            w = idf / idf.sum()
            for i, e in enumerate(j_ents):
                s = float(sim[i, best[i]]) if r_ents else 0.0
                requirements.append({
                    "skill": e, "found_by": j_src[e], "weight": float(w[i]),
                    "best_match": r_ents[best[i]] if r_ents else None, "similarity": s,
                    "contribution": float(w[i] * s), "lost": float(w[i] * (1 - s)),
                })
            # = scorer.score(resume, jd): IDF-weighted MaxSim (0 when the resume has no entities)
            score = float(sum(r["contribution"] for r in requirements))
            suggestions = self._suggestions(resume, jd)
        cal = self.art["calibration"]
        return {
            "score": score,
            "calibration": {
                "percentile_vs_relevant": _percentile(score, cal["relevant"]["quantiles"]),
                "percentile_vs_irrelevant": _percentile(score, cal["irrelevant"]["quantiles"]),
                "relevant_median": cal["relevant"]["quantiles"][50],
                "irrelevant_median": cal["irrelevant"]["quantiles"][50],
                "n_relevant": cal["relevant"]["n"], "n_irrelevant": cal["irrelevant"]["n"],
            },
            "requirements": requirements,
            "resume_skills": [{"skill": e, "found_by": r_src[e]} for e in r_ents],
            "suggestions": suggestions,
            "suggestion_band": self.art["nearmiss"]["band"],
            "empty_resume": not r_ents,
        }

    def _suggestions(self, resume: str, jd: str) -> list[dict]:
        """Phase 6 near-miss rule: JD ESCO concept whose best resume concept sim is in [lo, hi)."""
        from research.experiments.nearmiss_sweep import esco_concepts

        lo, hi = self.art["nearmiss"]["band"]
        r_spans, j_spans = self.esco.extract_batch([resume, jd])
        rc, jc = esco_concepts(r_spans), esco_concepts(j_spans)
        if not rc or not jc:
            return []
        ru, ju = list(rc), list(jc)
        strings = list(dict.fromkeys([rc[u] for u in ru] + [jc[u] for u in ju]))
        vec = dict(zip(strings, self.nm_encoder.encode(strings)))
        sim = np.stack([vec[jc[u]] for u in ju]) @ np.stack([vec[rc[u]] for u in ru]).T
        out = []
        for i, u in enumerate(ju):
            j = int(sim[i].argmax())
            s = float(sim[i, j])
            if lo <= s < hi:
                out.append({"jd_skill": jc[u], "resume_phrase": rc[ru[j]], "similarity": s,
                            "jd_concept": u, "resume_concept": ru[j]})
        return sorted(out, key=lambda d: -d["similarity"])

    # --- counterfactual check -----------------------------------------------------------------
    def _perturbers(self):
        if self._perturb is None:
            import spacy

            from research.common.config import load_config
            from research.perturbations.names import NameResources, NameSwap, build_name_resources
            from research.perturbations.registry import build_conditions, build_parts

            pcfg = load_config("configs/perturbations.yaml")
            nlp = spacy.load(pcfg["spacy_model"])
            try:
                res, names_ok = build_name_resources(pcfg["names"]), True
            except (FileNotFoundError, OSError):        # name lists are a manual download
                empty = {"F": [], "M": []}
                res, names_ok = NameResources({}, {"us": dict(empty), "in": dict(empty)}), False
            parts = build_parts(pcfg, nlp, name_resources=res)
            conds = build_conditions(pcfg, parts)
            if not names_ok:
                conds = [c for c in conds if not any(isinstance(p, NameSwap) for p in c.parts)]
            detector = NameSwap(res, "us", "opposite", float(pcfg["names"].get("min_share", 0.95)),
                                subject_only=bool(pcfg["names"].get("subject_only", True)))
            self._perturb = (nlp, conds, detector, names_ok)
        return self._perturb

    @staticmethod
    def _gender_from(doc, detector) -> str | None:
        """Gender of the resume's subject from a strongly gendered first name, else pronouns."""
        named = {g: len(detector.candidate_tokens(doc, g)) for g in ("F", "M")}
        if named["F"] != named["M"]:
            return "F" if named["F"] > named["M"] else "M"
        fem = sum(t.lower_ in ("she", "her", "hers", "herself") for t in doc)
        mas = sum(t.lower_ in ("he", "him", "his", "himself") for t in doc)
        if fem != mas:
            return "F" if fem > mas else "M"
        return None

    def counterfactual(self, resume: str, jd: str, conditions: list[str] | None = None) -> dict:
        resume, jd = layout_to_sentences(resume), layout_to_sentences(jd)
        with self.lock:
            from research.perturbations.names import NameSwap
            from research.perturbations.registry import Condition

            nlp, conds, detector, names_ok = self._perturbers()
            doc = nlp(resume)
            gender = self._gender_from(doc, detector)
            key = hashlib.sha256(resume.encode("utf-8")).hexdigest()[:16]
            scorers = {"entity_li": self.scorer, **self.compare}
            sd = self.art["pool_sd_dev_median"]
            label = lambda name: CONDITION_LABELS.get(name, name)  # noqa: E731
            results, rows = [], []
            for c in conds:
                if conditions and c.name not in conditions:
                    continue
                # name parts need the subject's gender; without one, only gender-free parts apply
                parts = c.parts if gender else [p for p in c.parts if not isinstance(p, NameSwap)]
                if not parts:
                    rows.append({"condition": c.name, "label": label(c.name), "changed": False,
                                 "skipped": "no gendered first name or pronouns found", "changes": [],
                                 "perturbed_text": resume, "scores": []})
                    continue
                results.append((c.name, Condition(c.name, parts).apply(doc, gender or "", key)))
            # one batched call per scorer: original + every changed version (JD extracted once)
            texts = [resume] + [r.text for _, r in results if r.changed]
            batch = {n: [float(x) for x in s.score_batch([(t, jd) for t in texts])] for n, s in scorers.items()}
            originals = {n: v[0] for n, v in batch.items()}
            i = 0
            for name, r in results:
                if r.changed:
                    i += 1
                scores = []
                for n in scorers:
                    new = batch[n][i] if r.changed else originals[n]
                    scores.append({"scorer": n, "original": originals[n], "perturbed": new,
                                   "delta": new - originals[n], "delta_norm": (new - originals[n]) / sd[n]})
                rows.append({"condition": name, "label": label(name), "changed": r.changed, "skipped": None,
                             "perturbed_text": r.text, "scores": scores,
                             "changes": [{"kind": ch.kind, "original": ch.original, "replacement": ch.replacement}
                                         for ch in r.changes]})
        order = {c.name: k for k, c in enumerate(conds)}
        rows.sort(key=lambda d: order[d["condition"]])
        return {"detected_gender": gender, "names_available": names_ok, "conditions": rows,
                "scorers": {"entity_li": "Entity-level late interaction (this app, the paper's method)",
                            "sbert_minilm": "Full-text embedding (MiniLM), a common baseline",
                            "backend_match": "This app's previous matcher (noun chunks, MiniLM, 0.55 threshold)"},
                "pool_sd": {n: sd[n] for n in scorers}}

    def info(self) -> dict:
        a = self.art
        return {"scorer": a["method"]["scorer"], "idf_docs": a["idf"]["n_docs"],
                "nearmiss": a["nearmiss"], "calibration_split": a["calibration"]["split"],
                "provenance": a["provenance"]}


_engine: MatchEngine | None = None
_error: str | None = None
_init_lock = threading.Lock()


def get_engine() -> MatchEngine:
    """Load once per process (about a minute: tagger, ESCO ruler, JobBERT-v2, MiniLM)."""
    global _engine, _error
    with _init_lock:
        if _engine is None:
            try:
                _engine = MatchEngine()
                _error = None
            except EngineUnavailable as e:
                _error = str(e)
                raise
        return _engine


def status() -> dict:
    return {"ready": _engine is not None, "loading": _init_lock.locked() and _engine is None, "error": _error}
