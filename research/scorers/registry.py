"""Build and fit scorers from config so every experiment uses the same code path.

A scorer spec is one entry of ``cfg['scorers']``:
    {name, type, enabled?, ...type-specific keys}
Types: bm25 | tfidf | sbert | cross_encoder | llm_judge | entity.
Encoders referenced by ``backbone`` come from ``cfg['backbones']``.
``cfg['persist_cache'] = False`` (used by the web app) turns off the on-disk embedding and
extraction caches, so texts being scored are never written to disk.
"""

from __future__ import annotations

from typing import Sequence

from research.common.config import repo_path
from research.common.embedding_cache import CachedEncoder
from research.common.seed import get_device

from .base import Scorer


def build_encoder(bspec: dict, cfg: dict, device: str) -> CachedEncoder:
    return CachedEncoder(
        bspec["model"], device=device, revision=bspec.get("revision"),
        max_seq_length=bspec.get("max_seq_length"), task=bspec.get("task"),
        batch_size=int(bspec.get("batch_size", cfg.get("embedding", {}).get("batch_size", 64))),
        normalize=True,
        cache_dir=repo_path(cfg["paths"]["embedding_cache"]) if cfg.get("persist_cache", True) else None,
    )


def build_extractor_for_scoring(espec: dict, cfg: dict):
    """An extractor wrapped in the on-disk extraction cache.

    ``type: union`` with ``members: [spec, ...]`` merges several (each cached separately).
    """
    from research.common.config import load_config

    if espec["type"] == "union":
        from research.extraction.union import UnionExtractor

        return UnionExtractor([build_extractor_for_scoring(m, cfg) for m in espec["members"]],
                              name=espec.get("name", "union"))
    from research.extraction.cache import CachedExtractor, spec_fingerprint
    from research.extraction.registry import build_extractor

    ecfg = load_config(cfg.get("extraction_config", "configs/extraction.yaml"))
    ecfg["device"] = cfg.get("device", "auto")
    extra = {k: ecfg.get(k) for k in ("spacy_model", "noun_chunk_filter", "esco_ruler")}
    ex = build_extractor({"name": espec.get("name", espec["type"]), **espec}, ecfg)
    if not cfg.get("persist_cache", True):
        return ex
    return CachedExtractor(ex, f"{espec.get('name', espec['type'])}|{spec_fingerprint(espec, extra)}")


def build_scorer(spec: dict, cfg: dict) -> Scorer:
    kind, name = spec["type"], spec["name"]
    device = get_device(cfg.get("device", "auto"))
    if kind == "bm25":
        from .lexical import BM25Scorer

        return BM25Scorer(k1=spec.get("k1", 1.5), b=spec.get("b", 0.75), epsilon=spec.get("epsilon", 0.25),
                          remove_stopwords=spec.get("remove_stopwords", True), name=name)
    if kind == "tfidf":
        from .lexical import TfidfScorer

        return TfidfScorer(sublinear_tf=spec.get("sublinear_tf", True), min_df=spec.get("min_df", 1),
                           remove_stopwords=spec.get("remove_stopwords", True), name=name)
    if kind == "sbert":
        from .dense import FullTextSBERTScorer

        enc = build_encoder(cfg["backbones"][spec["backbone"]], cfg, device)
        return FullTextSBERTScorer(enc, long_text=spec.get("long_text", "chunk_mean"),
                                   window_tokens=spec.get("window_tokens"), name=name)
    if kind == "cross_encoder":
        from .pairwise import CrossEncoderScorer

        return CrossEncoderScorer(spec["model"], spec.get("revision"), device, spec.get("max_length", 512),
                                  spec.get("batch_size", 32), name=name)
    if kind == "llm_judge":
        from .pairwise import DEFAULT_PROMPT, LLMJudgeScorer

        return LLMJudgeScorer(spec["model"], spec.get("revision"), device, spec.get("prompt", DEFAULT_PROMPT),
                              spec.get("max_new_tokens", 8), spec.get("max_input_tokens", 1536),
                              spec.get("batch_size", 4), name=name)
    if kind == "entity":
        from .entity import EntityLateInteractionScorer

        enc = build_encoder(cfg["backbones"][spec["backbone"]], cfg, device)
        ex = build_extractor_for_scoring(spec["extractor"], cfg)
        return EntityLateInteractionScorer(ex, enc, aggregation=spec.get("aggregation", "maxsim_mean"),
                                           labels=spec.get("labels"), sources=spec.get("sources"),
                                           dedupe=spec.get("dedupe", "casefold"),
                                           threshold=spec.get("threshold"), name=name)
    raise ValueError(f"unknown scorer type {kind!r}")


def build_scorers(cfg: dict, only: Sequence[str] | None = None) -> list[Scorer]:
    out = []
    for spec in cfg["scorers"]:
        if only is not None and spec["name"] not in only:
            continue
        if only is None and not spec.get("enabled", True):
            continue
        out.append(build_scorer(spec, cfg))
    return out


def fit_scorer(scorer, lexical_corpus: Sequence[str], jd_corpus: Sequence[str]) -> None:
    """Fit corpus statistics where a scorer needs them (lexical IDF, entity IDF)."""
    from .entity import EntityLateInteractionScorer
    from .lexical import BM25Scorer, TfidfScorer

    if isinstance(scorer, (BM25Scorer, TfidfScorer)):
        scorer.fit(lexical_corpus)
    elif isinstance(scorer, EntityLateInteractionScorer) and scorer.aggregation == "idf_weighted":
        scorer.fit(jd_corpus)
