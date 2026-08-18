from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8)
    roles: set[UserRole] = Field(default_factory=set)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    roles: set[UserRole] | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    roles: set[UserRole]
    active: bool


class UserListResponse(BaseModel):
    items: list[UserResponse]
    page: int
    page_size: int
    total: int


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    