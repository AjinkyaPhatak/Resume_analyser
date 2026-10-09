"""Scorers. Fast tests use fake encoders/extractors; @slow tests load the real models."""

import math
from pathlib import Path

import numpy as np
import pytest

from research.common.pair_cache import JsonCache, PairScoreCache
from research.extraction.base import TypedSpan
from research.extraction.cache import CachedExtractor
from research.scorers.aggregation import aggregate, hungarian, idf_table, idf_weighted, maxsim_mean, threshold_fraction
from research.scorers.base import Scorer
from research.scorers.dense import FullTextSBERTScorer, token_windows
from research.scorers.entity import EntityLateInteractionScorer
from research.scorers.lexical import BM25Scorer, TfidfScorer, make_tokenizer
from research.scorers.pairwise import _CachedPairScorer, parse_score

NURSE = ("Registered nurse with eight years of ICU experience in patient care, medication "
         "administration and wound care.")
SWE = ("Senior software engineer building distributed backend services in Java and Kubernetes; "
       "designs REST APIs and CI pipelines.")
JD = ("We are hiring a registered nurse for our intensive care unit. Responsibilities include "
      "patient care, administering medication and wound care.")
CORPUS = [NURSE, SWE, JD, "Teacher of mathematics at a secondary school.", "Accountant handling tax returns."]


# --- aggregation -------------------------------------------------------------------

SIM = np.array([[0.9, 0.1, 0.2],
                [0.8, 0.3, 0.1]])   # 2 JD entities x 3 resume entities


def test_maxsim_mean():
    assert maxsim_mean(SIM) == pytest.approx((0.9 + 0.8) / 2)


def test_hungarian_is_one_to_one():
    # both JD entities want resume entity 0; one-to-one forces the second to its next best
    assert hungarian(SIM) == pytest.approx((0.9 + 0.3) / 2)
    assert hungarian(SIM) < maxsim_mean(SIM)


def test_hungarian_more_jd_than_resume_entities():
    sim = np.array([[0.9], [0.8]])
    assert hungarian(sim) == pytest.approx(0.9 / 2)   # unassigned JD entity counts 0


def test_idf_weighted():
    assert idf_weighted(SIM, np.array([3.0, 1.0])) == pytest.approx(0.75 * 0.9 + 0.25 * 0.8)
    with pytest.raises(ValueError):
        idf_weighted(SIM, np.array([0.0, 0.0]))


def test_threshold_fraction():
    assert threshold_fraction(SIM, 0.85) == 0.5
    assert aggregate(SIM, "threshold_fraction", threshold=0.5) == 1.0


def test_aggregate_errors():
    with pytest.raises(ValueError):
        aggregate(np.zeros((0, 3)), "maxsim_mean")
    with pytest.raises(ValueError):
        aggregate(SIM, "nope")
    with pytest.raises(ValueError):
        aggregate(SIM, "idf_weighted")


def test_idf_table():
    table, unseen = idf_table([{"python", "sql"}, {"python"}, {"java"}])
    assert table["python"] < table["sql"] == table["java"] < unseen


# --- lexical -------------------------------------------------------------------------

def test_tokenizer_keeps_cpp_and_drops_pronouns():
    tok = make_tokenizer(True)
    assert tok("She knows C++ and C#; he uses Python.") == ["knows", "c++", "c#", "uses", "python"]
    assert "she" in make_tokenizer(False)("She knows")


def test_bm25_matches_rank_bm25():
    from rank_bm25 import BM25Okapi

    s = BM25Scorer().fit(CORPUS)
    docs = [s.tokenize(t) for t in CORPUS]
    ref = BM25Okapi(docs, k1=1.5, b=0.75, epsilon=0.25).get_scores(s.tokenize(JD))
    ours = [s.score(t, JD) for t in CORPUS]
    np.testing.assert_allclose(ours, ref, rtol=1e-9)


@pytest.mark.parametrize("cls", [BM25Scorer, TfidfScorer])
def test_lexical_match_beats_mismatch(cls):
    s = cls().fit(CORPUS)
    assert isinstance(s, Scorer)
    a, b = s.score_batch([(NURSE, JD), (SWE, JD)])
    assert a > b
    assert s.score(NURSE, JD) == pytest.approx(a)


def test_lexical_requires_fit():
    with pytest.raises(RuntimeError):
        BM25Scorer().score(NURSE, JD)
    with pytest.raises(RuntimeError):
        TfidfScorer().score(NURSE, JD)


def test_bm25_unseen_resume_tokens_ok():
    s = BM25Scorer().fit(CORPUS)
    assert s.score("Zyxwv qwerty nurse", JD) > 0   # perturbed text with unseen words still scores


# --- fakes ----------------------------------------------------------------------------

class WordHashEncoder:
    """Deterministic bag-of-words encoder: texts sharing words have higher cosine."""

    max_seq_length = 8

    def __init__(self, dim=256):
        self.dim = dim
        self.calls = 0

    def encode(self, texts):
        self.calls += 1
        out = np.zeros((len(texts), self.dim))
        for i, t in enumerate(texts):
            for w in t.lower().replace(";", " ").replace(",", " ").replace(".", " ").split():
                out[i, sum(map(ord, w)) % self.dim] += 1.0  # stable across processes
        n = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.clip(n, 1e-12, None)

    @property
    def tokenizer(self):
        def tok(text, add_special_tokens=False, return_offsets_mapping=True, verbose=True):
            offs, pos = [], 0
            for w in text.split():
                i = text.index(w, pos)
                offs.append((i, i + len(w)))
                pos = i + len(w)
            return {"offset_mapping": offs}
        return tok


class KeywordExtractor:
    """Fake extractor: every word in a fixed vocabulary is a 'knowledge' span."""

    name = "kw"
    VOCAB = {"nurse", "icu", "patient", "care", "medication", "wound", "java", "kubernetes",
             "apis", "backend", "she", "he"}

    def __init__(self):
        self.calls = 0

    def extract(self, text):
        return self.extract_batch([text])[0]

    def extract_batch(self, texts):
        self.calls += len(texts)
        out = []
        for t in texts:
            spans = []
            for i, w in enumerate(t.replace(",", " ").replace(".", " ").replace(";", " ").split()):
                if w.lower() in self.VOCAB:
                    label = "verb_phrase" if w.lower() in {"she", "he"} else "knowledge"
                    spans.append(TypedSpan(i, i + 1, w, label, "model"))
            out.append(spans)
        return out


# --- dense --------------------------------------------------------------------------

def test_token_windows():
    enc = WordHashEncoder()
    assert token_windows("a b c d e", enc.tokenizer, 2) == ["a b", "c d", "e"]
    assert token_windows("   ", enc.tokenizer, 2) == []
    with pytest.raises(ValueError):
        token_windows("a", enc.tokenizer, 0)


@pytest.mark.parametrize("mode", ["chunk_mean", "truncate"])
def test_fulltext_match_beats_mismatch(mode):
    s = FullTextSBERTScorer(WordHashEncoder(), long_text=mode, window_tokens=6)
    a, b = s.score_batch([(NURSE, JD), (SWE, JD)])
    assert a > b and -1.0 <= b <= a <= 1.0 + 1e-9


# --- entity scorer -----------------------------------------------------------------

def test_entity_scorer_match_beats_mismatch():
    s = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder())
    a, b = s.score_batch([(NURSE, JD), (SWE, JD)])
    assert a > b
    assert a == pytest.approx(1.0)   # every JD keyword appears in the nurse resume


def test_entity_scorer_label_filter_ignores_pronouns():
    s = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder(), labels=["knowledge"])
    assert s.score("She is a nurse", JD) == pytest.approx(s.score("He is a nurse", JD))
    s_all = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder(), labels=None)
    assert "she" in [e.lower() for e in s_all.entities_batch(["She is a nurse"])[0]]


def test_entity_scorer_empty_counts():
    s = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder())
    assert s.score("Nothing relevant here", JD) == 0.0
    assert s.n_empty == 1


def test_entity_scorer_dedupe_modes():
    ex = KeywordExtractor()
    assert EntityLateInteractionScorer(ex, WordHashEncoder(), dedupe="casefold").entities_batch(["Nurse nurse"])[0] == ["Nurse"]
    assert EntityLateInteractionScorer(ex, WordHashEncoder(), dedupe="exact").entities_batch(["Nurse nurse"])[0] == ["Nurse", "nurse"]


@pytest.mark.parametrize("agg", ["maxsim_mean", "hungarian", "idf_weighted", "threshold_fraction"])
def test_entity_scorer_aggregations(agg):
    s = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder(), aggregation=agg, threshold=0.9)
    if agg == "idf_weighted":
        with pytest.raises(RuntimeError):
            s.score(NURSE, JD)
        s.fit([JD, "We need a backend engineer who knows Java and Kubernetes."])
    a, b = s.score_batch([(NURSE, JD), (SWE, JD)])
    assert a > b


def test_entity_scorer_explain():
    out = EntityLateInteractionScorer(KeywordExtractor(), WordHashEncoder()).explain(NURSE, JD)
    assert out["matches"] and all(m[2] == pytest.approx(1.0) for m in out["matches"])


# --- caches ---------------------------------------------------------------------------

def test_cached_extractor_only_runs_misses(tmp_path):
    inner = KeywordExtractor()
    ex = CachedExtractor(inner, "kw|test", cache_dir=tmp_path)
    first = ex.extract_batch([NURSE, JD, NURSE])
    assert inner.calls == 2
    again = CachedExtractor(KeywordExtractor(), "kw|test", cache_dir=tmp_path)
    assert again.extract_batch([JD]) == [first[1]]
    assert again.extractor.calls == 0


def test_json_cache_roundtrip(tmp_path):
    c = JsonCache("ns", tmp_path)
    c.put_many({"a": [1, {"x": "y"}]})
    assert c.get_many(["a", "b"]) == {next(iter(c.get_many(["a"]))): [1, {"x": "y"}]}


class _Fake(_CachedPairScorer):
    def __init__(self, tmp, value):
        self.cache = PairScoreCache("fake", tmp)
        self.value, self.calls = value, 0

    def _compute(self, pairs):
        self.calls += len(pairs)
        return [self.value] * len(pairs)


def test_pair_cache_and_nan(tmp_path):
    s = _Fake(tmp_path, math.nan)
    assert math.isnan(s.score("r", "j"))
    s2 = _Fake(tmp_path, 1.0)
    assert math.isnan(s2.score("r", "j")) and s2.calls == 0     # NaN cached, not retried
    assert s2.score_batch([("r2", "j"), ("r2", "j")]) == [1.0, 1.0] and s2.calls == 1


# --- LLM output parsing ------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("85", 85.0), (" Score: 72", 72.0), ("I'd say 60/100.", 60.0), ("score = 99.5", 99.5),
    ("The candidate scores 7 out of 100", 7.0), ("2024 experience, score 40", 40.0),
    ("no idea", math.nan), ("150", math.nan), ("", math.nan),
])
def test_parse_score(text, expected):
    v = parse_score(text)
    assert (math.isnan(v) and math.isnan(expected)) or v == expected


# --- registry -----------------------------------------------------------------------

def test_registry_builds_configured_scorers():
    from research.common.config import load_config
    from research.scorers.registry import build_scorer

    cfg = load_config("configs/scorers.yaml")
    names = [s["name"] for s in cfg["scorers"]]
    assert {"bm25", "tfidf", "sbert_minilm", "sbert_mpnet", "jobbert_v2", "cross_encoder",
            "llm_judge", "backend_match", "entity_li"} <= set(names)
    assert not next(s for s in cfg["scorers"] if s["name"] == "llm_judge")["enabled"]
    bm = build_scorer(next(s for s in cfg["scorers"] if s["name"] == "bm25"), cfg)
    assert bm.name == "bm25"
    with pytest.raises(ValueError):
        build_scorer({"name": "x", "type": "bogus"}, cfg)


# --- real models (slow) -------------------------------------------------------------

@pytest.fixture(scope="module")
def scorer_cfg():
    from research.common.config import load_config

    return load_config("configs/scorers.yaml")


@pytest.mark.slow
@pytest.mark.parametrize("name", ["sbert_minilm", "sbert_mpnet", "jobbert_v2", "cross_encoder",
                                  "backend_match", "entity_li"])
def test_real_scorer_match_beats_mismatch(scorer_cfg, name):
    from research.scorers.registry import build_scorer

    spec = next(s for s in scorer_cfg["scorers"] if s["name"] == name)
    s = build_scorer(spec, scorer_cfg)
    a, b = s.score_batch([(NURSE, JD), (SWE, JD)])
    assert a > b, (name, a, b)


@pytest.mark.slow
def test_backend_match_reproduces_backend(scorer_cfg):
    from research.legacy.backend_matcher_60bfe79 import semantic_match
    from research.scorers.registry import build_scorer

    s =build_scorer(next(x for x in scorer_cfg["scorers"] if x["name"] == "backend_match"), scorer_cfg)
    for resume in (NURSE, SWE):
        ours = s.score(resume, JD)
        theirs = semantic_match(resume, JD)["match_percent"] / 100
        assert ours == pytest.approx(theirs, abs=0.0015)   # backend rounds to 0.1 %


def test_union_extractor_merges_and_dedupes():
    from research.extraction.union import UnionExtractor

    class Fixed:
        def __init__(self, spans):
            self.spans = spans

        def extract_batch(self, texts):
            return [list(self.spans) for _ in texts]

    a = TypedSpan(0, 1, "python", "knowledge", "model")
    b = TypedSpan(0, 1, "python", "skill", "esco")       # same boundaries -> first member wins
    c = TypedSpan(2, 4, "data analysis", "skill", "esco")
    out = UnionExtractor([Fixed([a]), Fixed([b, c])]).extract("x")
    assert out == [a, c]
    with pytest.raises(ValueError):
        UnionExtractor([])
