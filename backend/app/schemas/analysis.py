from pydantic import BaseModel

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str

class MatchResponse(BaseModel):
    match_percent: float
    matched_skills: list[dict]
    missing_skills: list[str]
    total_jd_skills: int
    total_matched: int

class BiasRequest(BaseModel):
    text: str

class BiasResponse(BaseModel):
    bias_score: float
    flagged_words: list[dict]
    verdict: str