"""Endpoint tests for /analysis. Run from backend/: python -m pytest tests"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

RESUME = "Built REST APIs in Python and deployed Docker containers on AWS. Led a team of engineers."
JD = "We need a Python developer with REST API design and AWS experience."


def test_match_returns_frontend_schema():
    r = client.post("/analysis/match", json={"resume_text": RESUME, "jd_text": JD})
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("match_percent", "matched_skills", "missing_skills", "total_jd_skills", "total_matched"):
        assert key in body
    assert 0 <= body["match_percent"] <= 100
    assert body["total_matched"] == len(body["matched_skills"])
    assert body["total_jd_skills"] == body["total_matched"] + len(body["missing_skills"])
    for m in body["matched_skills"]:
        assert set(m) == {"jd_skill", "resume_match", "score"}


def test_match_empty_input_is_400():
    r = client.post("/analysis/match", json={"resume_text": "", "jd_text": JD})
    assert r.status_code == 400


def test_bias_endpoint():
    r = client.post("/analysis/bias", json={"text": "We want an aggressive, competitive leader."})
    assert r.status_code == 200
    body = r.json()
    assert body["bias_score"] > 0
    assert any(f["type"] == "masculine-coded" for f in body["flagged_words"])
