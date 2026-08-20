"""JWT security helpers."""

import os
from typing import Any

from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")


def create_access_token(data: dict[str, Any]) -> str:
    # TODO: Create a signed JWT access token.
    pass


def verify_access_token(token: str) -> dict[str, Any] | None:
    # TODO: Verify and decode a JWT access token.
    pass
