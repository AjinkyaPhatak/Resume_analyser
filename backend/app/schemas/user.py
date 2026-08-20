"""User-related API schemas."""

from pydantic import BaseModel


class UserCreate(BaseModel):
    # TODO: Add registration fields.
    pass


class UserLogin(BaseModel):
    # TODO: Add login credential fields.
    pass


class UserResponse(BaseModel):
    # TODO: Add safe user response fields.
    pass
