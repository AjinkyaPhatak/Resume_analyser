"""Authentication API routes."""

from fastapi import APIRouter

from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate) -> UserResponse:
    # TODO: Register a new user.
    pass


@router.post("/login")
async def login_user(credentials: UserLogin) -> None:
    # TODO: Authenticate the user and return an access token.
    pass
