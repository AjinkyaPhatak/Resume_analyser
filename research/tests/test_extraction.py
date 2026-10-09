from pathlib import Path

import pytest

from research.data.skillspan import bio_to_spans, load_split
from research.extraction.base import Extractor, TypedSpan, dedupe_spans
from research.extraction.esco import EscoExtractor, build_patterns, load_esco_skills
from research.extraction.filters import NounChunkFilter
from research.extraction.noun_chunk import FilteredNounChunkExtractor, NounChunkExtractor
from research.metrics.span_metrics import PRFCounter, SpanEvaluator

FIX = Path(__file__).parent / "fixtures"
ESCO_CSV = FIX / "esco_skills_tiny.csv"


# --- SkillSpan loading --------------------------------------------------------------

@pytest.mark.parametrize(
    "tags, expected",
    [
        (["O", "O"], []),
        (["B", "I", "O", "B"], [(0, 2), (3, 4)]),
        (["B", "B", "I"], [(0, 1), (1, 3)]),
        (["I", "I", "O"], [(0, 2)]),          # I without B opens a span
        (["B-SKILL", "I-SKILL"], [(0, 2)]),   # typed tags tolerated
    ],
)
def test_bio_to_spans(tags, expected):
    assert bio_to_spans(tags) == expected


def test_bio_rejects_bad_tag():
    with pytest.raises(ValueError):
        bio_to_spans(["B", "X"])


def test_load_skillspan_fixture():
    sents = load_split(FIX / "skillspan_tiny.json")
    assert len(sents) == 3
    assert sents[0].skill == ((0, 2),)
    assert sents[0].knowledge == ((4, 5),)
    assert sents[0].all_spans == {(0, 2), (4, 5)}
    assert sents[2].source == "tech"


# --- span metrics -----------------------------------------------------------------------

def test_exact_metrics():
    c = PRFCounter()
    c.add(pred=[(0, 2), (3, 4)], gold=[(0, 2), (5, 7)], mode="exact")
    assert (c.precision, c.recall, c.f1) == (0.5, 0.5, 0.5)


def test_partial_metrics_counts_p_and_r_separately():
    c = PRFCounter()
    # two short preds inside one long gold span: both correct for P, gold found once
    c.add(pred=[(0, 1), (2, 3), (8, 9)], gold=[(0, 4), (5, 6)], mode="partial")
    assert c.precision == pytest.approx(2 / 3)
    assert c.recall == pytest.approx(1 / 2)


def test_metrics_empty_is_zero_not_error():
    c = PRFCounter()
    c.add([], [], "exact")
    assert (c.precision, c.recall, c.f1) == (0.0, 0.0, 0.0)


def test_duplicate_spans_collapsed():
    c = PRFCounter()
    c.add([(0, 1), (0, 1)], [(0, 1)], "exact")
    assert c.n_pred == 1 and c.f1 == 1.0


def test_span_evaluator_views():
    ev = SpanEvaluator()
    pred = [TypedSpan(0, 2, "manage budgets", "skill", "esco"), TypedSpan(4, 5, "Python", "knowledge", "esco")]
    ev.add(pred, {"all": {(0, 2), (4, 5)}, "skill": [(0, 2)], "knowledge": [(4, 5)]}, group="house")
    by = {(r["group"], r["view"], r["mode"]): r for r in ev.rows()}
    assert by[("all", "all", "exact")]["f1"] == 1.0
    assert by[("house", "skill", "exact")]["f1"] == 1.0
    assert by[("all", "knowledge", "exact")]["n_pred"] == 1


# --- span type ------------------------------------------------------------------------

def test_typed_span_validation():
    with pytest.raises(ValueError):
        TypedSpan(0, 1, "x", "bogus", "esco")
    with pytest.raises(ValueError):
        TypedSpan(2, 2, "x", "skill", "esco")


def test_dedupe_keeps_first_and_sorts():
    a = TypedSpan(3, 4, "b", "knowledge", "esco")
    b = TypedSpan(0, 1, "a", "skill", "esco")
    c = TypedSpan(3, 4, "b", "knowledge", "noun_chunk")
    assert dedupe_spans([a, b, c]) == [b, a]
    assert dedupe_spans([a, b, c])[1].source == "esco"


# --- noun-chunk extractors ------------------------------------------------------------

@pytest.fixture(scope="module")
def nc():
    return NounChunkExtractor()


def test_noun_chunk_extracts_pronouns_like_backend(nc):
    texts = nc.texts("She is a nurse. She led a team at Mount Sinai.")
    assert "She" in texts          # the leakage path documented in BACKEND_AUDIT.md
    assert "led team at" in texts  # backend-style: head words of dobj + prep children


def test_noun_chunk_is_an_extractor(nc):
    assert isinstance(nc, Extractor)


def test_extract_tokens_preserves_offsets(nc):
    tokens = ["Experience", "with", "machine", "learning", "required"]
    spans = nc.extract_tokens(tokens)
    for s in spans:
        assert " ".join(tokens[s.start:s.end]) == s.text or s.source == "verb"


def test_verb_phrase_span_covers_children(nc):
    spans = [s for s in nc.extract("She led a team.") if s.source == "verb"]
    assert spans and spans[0].text == "led team"
    assert spans[0].end - spans[0].start == 3  # "led a team"


def test_filtered_nc_drops_pronouns_determiners_generics():
    ex = FilteredNounChunkExtractor(noun_chunk_filter=NounChunkFilter(generic_nouns=frozenset({"experience"})))
    texts = ex.texts("She has experience with the Kubernetes clusters and <ORGANIZATION> tools.")
    assert "She" not in texts
    assert "experience" not in texts
    assert "Kubernetes clusters" in texts      # determiner trimmed
    assert not any("<ORGANIZATION>" in t for t in texts)


def test_filtered_nc_empty_text():
    assert FilteredNounChunkExtractor().extract("") == []


@pytest.mark.slow
def test_parity_with_backend_extract_entities():
    """The research port must produce exactly the backend's strings."""
    import sys

    backend = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend))
    try:
        from app.services.matcher import extract_entities
    finally:
        sys.path.remove(str(backend))
    ex = NounChunkExtractor()
    for text in [
        "She is a nurse at Mount Sinai in New York. She led a team and deployed containers on AWS.",
        "We need a Python developer with REST API design and AWS experience. You will build data pipelines.",
        "Managed budgets; mentored junior engineers, and presented results to stakeholders.",
    ]:
        assert set(ex.texts(text)) == set(extract_entities(text))


# --- ESCO -----------------------------------------------------------------------------

def test_load_esco_fixture_filters_status():
    concepts = load_esco_skills(ESCO_CSV)
    uris = {c.uri for c in concepts}
    assert "http://example.org/esco/obsolete" not in uris
    py = next(c for c in concepts if c.uri.endswith("python"))
    assert py.label == "knowledge"
    assert "python programming" in py.surface_forms


def test_build_patterns_drops_stopwords_and_dupes():
    pats = build_patterns(load_esco_skills(ESCO_CSV))
    forms = [p["pattern"].lower() for p in pats]
    assert "the" not in forms and "it" not in forms and "a" not in forms
    assert len(forms) == len(set(forms))


def test_esco_missing_file_message(tmp_path):
    with pytest.raises(FileNotFoundError, match="manual download"):
        load_esco_skills(tmp_path / "nope.csv")


def test_esco_bad_columns(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="preferredLabel"):
        load_esco_skills(p)


@pytest.fixture(scope="module")
def esco():
    return EscoExtractor(ESCO_CSV)


def test_esco_case_insensitive_and_lemma(esco):
    spans = esco.extract("She was managing budgets and wrote PYTHON code for Machine Learning.")
    by_text = {s.text.lower(): s for s in spans}
    assert "managing budgets" in by_text               # lemma match to "manage budgets"
    assert by_text["managing budgets"].label == "skill"
    assert "python" in by_text and by_text["python"].label == "knowledge"
    assert by_text["machine learning"].concept_id == "http://example.org/esco/ml"
    assert all(s.source == "esco" for s in spans)
    assert "she" not in by_text


def test_esco_prefers_longest_match(esco):
    texts = esco.texts("Strong python programming skills.")
    assert "python programming" in texts and "python" not in texts


def test_esco_nc_adds_non_overlapping_chunks():
    ex = EscoExtractor(ESCO_CSV, noun_chunks=True)
    spans = ex.extract("She used Python to build Kubernetes clusters.")
    sources = {s.text: s.source for s in spans}
    assert sources.get("Python") == "esco"
    assert sources.get("Kubernetes clusters") == "noun_chunk"
    assert "She" not in sources


def test_esco_no_matches(esco):
    assert esco.extract("Nothing relevant here at all.") == []
