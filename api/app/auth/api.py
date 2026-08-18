from fastapi import APIRouter

from .schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    raise NotImplementedError


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    raise NotImplementedError

