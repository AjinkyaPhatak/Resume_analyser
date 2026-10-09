"""Endpoint tests for /analysis. Run from backend/: python -m pytest  (add -m slow for real models)

Fast tests replace the matcher with a stub (dependency override), so they check the API
contract without loading models. The slow tests load the real matcher and check that the
app's score equals the research scorer's.
"""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("RESUME_ANALYSER_NO_WARMUP", "1")

from app.routers import analysis  # noqa: E402
from app.services.bias import detect_bias  # noqa: E402
from app.services.engine import ARTIFACT, REPO_ROOT, _percentile, layout_to_sentences  # noqa: E402
from main import app  # noqa: E402

RESUME = ("Priya Shah is a data engineer. She built REST APIs in Python, deployed Docker containers on AWS "
          "and led a team of four engineers.")
JD = "We need a Python developer with REST API design, Docker and AWS experience."


class StubEngine:
    def match(self, resume, jd):
        req = {"skill": "Python", "found_by": ["ESCO taxonomy"], "weight": 1.0, "best_match": "Python",
               "similarity": 0.9, "contribution": 0.9, "lost": 0.1}
        cal = {"percentile_vs_relevant": 60.0, "percentile_vs_irrelevant": 90.0, "relevant_median": 0.41,
               "irrelevant_median": 0.35, "n_relevant": 10, "n_irrelevant": 90}
        return {"score": 0.9, "calibration": cal, "requirements": [req],
                "resume_skills": [{"skill": "Python", "found_by": ["ESCO taxonomy"]}],
                "suggestions": [], "suggestion_band": [0.65, 0.9], "empty_resume": False}

    def counterfactual(self, resume, jd, conditions=None):
        shift = {"scorer": "entity_li", "original": 0.9, "perturbed": 0.9, "delta": 0.0, "delta_norm": 0.0}
        row = {"condition": "pronoun_swap", "label": "Pronouns swapped", "changed": True, "skipped": None,
               "perturbed_text": resume.replace("She", "He"),
               "changes": [{"kind": "pronoun", "original": "She", "replacement": "He"}], "scores": [shift]}
        return {"detected_gender": "F", "names_available": True, "conditions": [row],
                "scorers": {"entity_li": "ours"}, "pool_sd": {"entity_li": 0.04}}

    def info(self):
        return {"scorer": {"name": "entity_li"}}


@pytest.fixture
def client():
    app.dependency_overrides[analysis.engine] = lambda: StubEngine()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_match_contract(client):
    r = client.post("/analysis/match", json={"resume_text": RESUME, "jd_text": JD})
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0 <= body["score"] <= 1
    assert {"skill", "weight", "best_match", "similarity", "contribution", "lost"} <= set(body["requirements"][0])


@pytest.mark.parametrize("resume,jd", [("", JD), (RESUME, "   "), ("x" * 30_001, JD)])
def test_match_rejects_bad_input(client, resume, jd):
    assert client.post("/analysis/match", json={"resume_text": resume, "jd_text": jd}).status_code == 400


def test_counterfactual_contract(client):
    r = client.post("/analysis/counterfactual", json={"resume_text": RESUME, "jd_text": JD})
    assert r.status_code == 200, r.text
    assert r.json()["conditions"][0]["changes"][0]["replacement"] == "He"


def test_missing_models_give_503(monkeypatch):
    def unavailable():
        raise analysis.engine_mod.EngineUnavailable("no model")

    monkeypatch.setattr(analysis.engine_mod, "get_engine", unavailable)
    r = TestClient(app).post("/analysis/match", json={"resume_text": RESUME, "jd_text": JD})
    assert r.status_code == 503 and "no model" in r.json()["detail"]


def test_status_endpoint():
    r = TestClient(app).get("/analysis/status")
    assert r.status_code == 200 and "ready" in r.json()


def test_percentile_handles_ties_and_ends():
    q = [0.0, 0.0, 0.0, 0.5, 1.0]            # 5 quantiles at levels 0, 25, 50, 75, 100
    assert _percentile(-1, q) == 0.0 and _percentile(2, q) == 100.0
    assert _percentile(0.0, q) == 0.0
    assert _percentile(0.25, q) == pytest.approx(62.5)
    assert _percentile(0.75, q) == pytest.approx(87.5)


def test_layout_to_sentences():
    assert layout_to_sentences("No line breaks here") == "No line breaks here"     # research texts
    out = layout_to_sentences("Jane Doe\nData Engineer\n\n\u2022 Built ETL pipelines\n- SQL, Python.")
    assert out == "Jane Doe.\nData Engineer.\nBuilt ETL pipelines.\nSQL, Python."


# --- bias (regressions for the Phase 0 audit) -----------------------------------------

def test_bias_endpoint():
    r = TestClient(app).post("/analysis/bias", json={"text": "We want an aggressive, competitive leader."})
    assert r.status_code == 200
    body = r.json()
    assert body["bias_score"] > 0 and body["masculine_count"] == 3
    assert all(f["type"] == "masculine-coded" for f in body["flagged_words"])


def test_bias_no_prefix_false_positives():
    assert detect_bias("kindergarten committee trustee warmup")["flagged_words"] == []


def test_bias_hyphenated_and_inflected_words_match():
    words = {f["word"]: f["matched"] for f in detect_bias("self-reliant leaders collaborating")["flagged_words"]}
    assert words == {"self-reliant": "self-reliant", "leaders": "lead", "collaborating": "collaborate"}


def test_bias_verdict_symmetric_at_cutoff():
    # exactly +1 coded word per 100 words used to be labelled "feminine-coded"
    text = "aggressive " + "word " * 99
    r = detect_bias(text)
    assert r["bias_score"] == 1.0 and "masculine" in r["verdict"].lower()
    r = detect_bias("kind " + "word " * 99)
    assert r["bias_score"] == -1.0 and "feminine" in r["verdict"].lower()


# --- real matcher -----------------------------------------------------------------------

def _models_present():
    return ARTIFACT.is_file() and (REPO_ROOT / "research/models/jobbert_skillspan/seed13/tagger_state.pt").is_file()


@pytest.mark.slow
@pytest.mark.skipif(not _models_present(), reason="needs research/models and backend/artifacts")
def test_real_match_equals_research_scorer():
    from app.services.engine import get_engine

    eng = get_engine()
    out = eng.match(RESUME, JD)
    assert out["score"] == pytest.approx(eng.scorer.score(RESUME, JD), abs=1e-6)
    assert abs(sum(r["weight"] for r in out["requirements"]) - 1) < 1e-6
    for s in out["suggestions"]:
        assert out["suggestion_band"][0] <= s["similarity"] < out["suggestion_band"][1]


@pytest.mark.slow
@pytest.mark.skipif(not _models_present(), reason="needs research/models and backend/artifacts")
def test_real_counterfactual_swaps_pronouns():
    from app.services.engine import get_engine

    out = get_engine().counterfactual(RESUME, JD, ["pronoun_swap"])
    row = out["conditions"][0]
    assert row["changed"] and "He built" in row["perturbed_text"]
    assert {s["scorer"] for s in row["scores"]} == {"entity_li", "sbert_minilm", "backend_match"}
