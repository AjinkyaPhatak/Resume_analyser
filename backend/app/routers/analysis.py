from fastapi import APIRouter, HTTPException
from app.schemas.analysis import MatchRequest, MatchResponse, BiasRequest, BiasResponse
from app.services.matcher import semantic_match
from app.services.bias import detect_bias

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/match", response_model=MatchResponse)
def match_resume(request: MatchRequest):
    result = semantic_match(request.resume_text, request.jd_text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/bias", response_model=BiasResponse)
def bias_check(request: BiasRequest):
    result = detect_bias(request.text)
    return result