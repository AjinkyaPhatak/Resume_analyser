from fastapi import APIRouter, Depends, HTTPException

from app.schemas.analysis import (
    BiasRequest, BiasResponse, CounterfactualRequest, CounterfactualResponse, MatchRequest, MatchResponse,
)
from app.services import engine as engine_mod
from app.services.bias import detect_bias

router = APIRouter(prefix="/analysis", tags=["analysis"])

MAX_CHARS = 30_000


def engine():
    """The loaded matcher; 503 with instructions if models/artifacts are missing."""
    try:
        return engine_mod.get_engine()
    except engine_mod.EngineUnavailable as e:
        raise HTTPException(status_code=503, detail=f"Matcher unavailable: {e}")


def _check(request: MatchRequest):
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="The resume text is empty.")
    if not request.jd_text.strip():
        raise HTTPException(status_code=400, detail="The job description is empty.")
    if max(len(request.resume_text), len(request.jd_text)) > MAX_CHARS:
        raise HTTPException(status_code=400, detail=f"Texts are limited to {MAX_CHARS:,} characters.")


@router.get("/status")
def matcher_status():
    return engine_mod.status()


@router.get("/method")
def method_info(eng=Depends(engine)):
    return eng.info()


@router.post("/match", response_model=MatchResponse)
def match_resume(request: MatchRequest, eng=Depends(engine)):
    _check(request)
    try:
        return eng.match(request.resume_text, request.jd_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/counterfactual", response_model=CounterfactualResponse)
def counterfactual(request: CounterfactualRequest, eng=Depends(engine)):
    _check(request)
    return eng.counterfactual(request.resume_text, request.jd_text, request.conditions)


@router.post("/bias", response_model=BiasResponse)
def bias_check(request: BiasRequest):
    return detect_bias(request.text)
