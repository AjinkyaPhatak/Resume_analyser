from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str


class Requirement(BaseModel):
    skill: str                    # JD skill entity
    found_by: list[str]           # extractors that proposed it
    weight: float                 # normalised IDF weight (sums to 1 over the JD's skills)
    best_match: str | None        # closest resume entity (MaxSim)
    similarity: float             # cosine similarity of that pair (JobBERT-v2)
    contribution: float           # weight * similarity; the score is their sum
    lost: float                   # weight * (1 - similarity)


class ResumeSkill(BaseModel):
    skill: str
    found_by: list[str]


class Suggestion(BaseModel):
    jd_skill: str
    resume_phrase: str
    similarity: float
    jd_concept: str               # ESCO concept URIs
    resume_concept: str


class Calibration(BaseModel):
    percentile_vs_relevant: float
    percentile_vs_irrelevant: float
    relevant_median: float
    irrelevant_median: float
    n_relevant: int
    n_irrelevant: int


class MatchResponse(BaseModel):
    score: float                  # IDF-weighted MaxSim, 0-1
    calibration: Calibration
    requirements: list[Requirement]
    resume_skills: list[ResumeSkill]
    suggestions: list[Suggestion]
    suggestion_band: list[float]
    empty_resume: bool


class CounterfactualRequest(MatchRequest):
    conditions: list[str] | None = None


class ScoreShift(BaseModel):
    scorer: str
    original: float
    perturbed: float
    delta: float
    delta_norm: float             # delta / median pool SD of that scorer on DEV (paper's units)


class TextChange(BaseModel):
    kind: str
    original: str
    replacement: str


class ConditionResult(BaseModel):
    condition: str
    label: str
    changed: bool
    skipped: str | None
    perturbed_text: str
    changes: list[TextChange]
    scores: list[ScoreShift]


class CounterfactualResponse(BaseModel):
    detected_gender: str | None
    names_available: bool
    conditions: list[ConditionResult]
    scorers: dict[str, str]
    pool_sd: dict[str, float]


class BiasRequest(BaseModel):
    text: str


class FlaggedWord(BaseModel):
    word: str
    type: str
    matched: str
    source: str


class BiasResponse(BaseModel):
    bias_score: float
    flagged_words: list[FlaggedWord]
    verdict: str
    masculine_count: int = 0
    feminine_count: int = 0
    n_words: int = Field(0, ge=0)
