"""Analysis request and response schemas."""

from pydantic import BaseModel


class MatchRequest(BaseModel):
    # TODO: Add resume and job-description input fields.
    pass


class MatchResponse(BaseModel):
    # TODO: Add semantic-match response fields.
    pass


class BiasRequest(BaseModel):
    # TODO: Add text input fields.
    pass


class BiasResponse(BaseModel):
    # TODO: Add bias-analysis response fields.
    pass
