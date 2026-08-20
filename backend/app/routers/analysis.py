"""Resume analysis API routes."""

from fastapi import APIRouter

from app.schemas.analysis import BiasRequest, BiasResponse, MatchRequest, MatchResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/match", response_model=MatchResponse)
async def match_resume(request: MatchRequest) -> MatchResponse:
    # TODO: Match resume content against a job description.
    pass


@router.post("/bias", response_model=BiasResponse)
async def analyse_bias(request: BiasRequest) -> BiasResponse:
    # TODO: Detect bias in the provided text.
    pass
