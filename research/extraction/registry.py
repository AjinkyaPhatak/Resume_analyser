"""Build extractors from config dicts so experiments and scorers share one code path."""

from __future__ import annotations

from research.common.config import repo_path

from .base import Extractor
from .filters import NounChunkFilter


def build_noun_chunk_filter(cfg: dict) -> NounChunkFilter:
    f = cfg.get("noun_chunk_filter", {})
    return NounChunkFilter(
        trim_pos=tuple(f.get("trim_pos", NounChunkFilter.trim_pos)),
        trim_stopwords=bool(f.get("trim_stopwords", True)),
        generic_nouns=frozenset(f.get("generic_nouns", [])),
        drop_regex=f.get("drop_regex"),
        min_chars=int(f.get("min_chars", 2)),
    )


def esco_csv_path(cfg: dict):
    spec = cfg["datasets"]["esco"]
    return repo_path(spec["local_dir"]) / spec["skills_csv"]


def build_extractor(spec: dict, cfg: dict) -> Extractor:
    """``spec`` is one entry of ``cfg['extractors']``: {name, type}."""
    kind = spec["type"]
    name = spec.get("name", kind)
    model = cfg.get("spacy_model", "en_core_web_sm")
    if kind == "noun_chunk":
        from .noun_chunk import NounChunkExtractor

        return NounChunkExtractor(spacy_model=model, name=name)
    if kind == "filtered_nc":
        from .noun_chunk import FilteredNounChunkExtractor

        return FilteredNounChunkExtractor(model, build_noun_chunk_filter(cfg), name=name)
    if kind in ("esco", "esco_nc"):
        from .esco import EscoExtractor

        r = cfg.get("esco_ruler", {})
        return EscoExtractor(
            esco_csv=esco_csv_path(cfg),
            spacy_model=model,
            match_attrs=tuple(r.get("match_attrs", ("lemma", "lower"))),
            include_alt_labels=bool(r.get("include_alt_labels", True)),
            include_hidden_labels=bool(r.get("include_hidden_labels", False)),
            min_label_chars=int(r.get("min_label_chars", 2)),
            max_label_tokens=int(r.get("max_label_tokens", 8)),
            drop_stopword_only=bool(r.get("drop_stopword_only", True)),
            exclude_labels=tuple(r.get("exclude_labels", [])),
            noun_chunks=(kind == "esco_nc"),
            noun_chunk_filter=build_noun_chunk_filter(cfg),
            name=name,
        )
    if kind == "token_classifier":
        from research.common.seed import get_device

        from .token_classifier import TokenClassifierExtractor

        model_dir = repo_path(spec["model_dir"])
        if not (model_dir / "tagger_state.pt").is_file():
            raise FileNotFoundError(
                f"No trained model at {model_dir}. Train it first: "
                "python -m research.experiments.train_extractor"
            )
        return TokenClassifierExtractor(model_dir, device=get_device(cfg.get("device", "auto")),
                                        max_length=int(spec.get("max_length", 256)), name=name)
    raise ValueError(f"Unknown extractor type {kind!r}")
