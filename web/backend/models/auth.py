"""Authentication and authorization models."""

from datetime import datetime

from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    """Authenticated user returned by the auth layer."""

    user_id: str
    username: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    # Login must accept legacy/admin-provisioned accounts that may predate
    # the current password policy. Account creation still enforces 8+ chars.
    password: str = Field(min_length=1, max_length=256)


class BootstrapRequest(LoginRequest):
    # Backend AuthService enforces MEDICAL_DEID_MIN_PASSWORD_LENGTH.
    password: str = Field(min_length=1, max_length=256)


class CreateUserRequest(LoginRequest):
    password: str = Field(min_length=1, max_length=256)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UpdateUserRequest(BaseModel):
    role: str | None = Field(default=None, pattern="^(admin|user)$")
    is_active: bool | None = None


class AuthResponse(BaseModel):
    user: AuthUser


__all__ = [
    "AuthResponse",
    "AuthUser",
    "BootstrapRequest",
    "CreateUserRequest",
    "LoginRequest",
    "UpdateUserRequest",
]
