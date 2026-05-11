"""Authentication API."""

import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from loguru import logger

from config import (
    AUTH_MODE,
    BOOTSTRAP_TOKEN,
    ENABLE_PUBLIC_BOOTSTRAP,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)
from models.auth import (
    AuthResponse,
    AuthUser,
    BootstrapRequest,
    CreateUserRequest,
    LoginRequest,
    UpdateUserRequest,
)
from security import get_current_user, require_admin_user
from services.auth_service import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
FAILED_LOGIN_WINDOW_SECONDS = 300
FAILED_LOGIN_LIMIT = 8
_failed_login_attempts: dict[str, list[float]] = defaultdict(list)


def _set_session_cookie(response: Response, token: str, expires_at) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        expires=expires_at,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite=SESSION_COOKIE_SAMESITE,
        secure=SESSION_COOKIE_SECURE,
        httponly=True,
    )


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_login_rate_limit(request: Request, username: str) -> None:
    now = time.time()
    key = f"{_client_ip(request)}:{username.strip().lower()}"
    attempts = [
        timestamp
        for timestamp in _failed_login_attempts[key]
        if now - timestamp < FAILED_LOGIN_WINDOW_SECONDS
    ]
    _failed_login_attempts[key] = attempts
    if len(attempts) >= FAILED_LOGIN_LIMIT:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts. Please retry later.",
        )


def _record_failed_login(request: Request, username: str) -> None:
    key = f"{_client_ip(request)}:{username.strip().lower()}"
    _failed_login_attempts[key].append(time.time())
    logger.warning(
        "Failed login attempt",
        username=username.strip(),
        client_ip=_client_ip(request),
    )


def _clear_failed_logins(request: Request, username: str) -> None:
    _failed_login_attempts.pop(f"{_client_ip(request)}:{username.strip().lower()}", None)


@router.get("/setup-required")
async def setup_required() -> dict[str, bool | str]:
    """Return whether the first admin account must be created."""
    return {
        "setup_required": False if AUTH_MODE == "anonymous_session" else get_auth_service().count_users() == 0,
        "auth_mode": AUTH_MODE,
    }


@router.post("/bootstrap", response_model=AuthResponse)
async def bootstrap_first_admin(
    payload: BootstrapRequest,
    request: Request,
    response: Response,
    x_bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
):
    """Create the first admin. Disabled after any user exists."""
    service = get_auth_service()
    if service.count_users() > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bootstrap already completed")
    if BOOTSTRAP_TOKEN:
        if not x_bootstrap_token or not secrets.compare_digest(x_bootstrap_token, BOOTSTRAP_TOKEN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid bootstrap token")
    elif not ENABLE_PUBLIC_BOOTSTRAP:
        logger.warning("Blocked public bootstrap attempt", client_ip=_client_ip(request))
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Public bootstrap is disabled. Configure bootstrap credentials in the service env.",
        )

    try:
        user = service.bootstrap_first_admin(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    token, expires_at = service.create_session(user.user_id)
    _set_session_cookie(response, token, expires_at)
    return AuthResponse(user=user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request, response: Response):
    """Login with username/password and set an HttpOnly session cookie."""
    _check_login_rate_limit(request, payload.username)
    user = get_auth_service().authenticate(payload.username, payload.password)
    if not user:
        _record_failed_login(request, payload.username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    _clear_failed_logins(request, payload.username)
    token, expires_at = get_auth_service().create_session(user.user_id)
    _set_session_cookie(response, token, expires_at)
    return AuthResponse(user=user)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    """Logout the current browser session."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        get_auth_service().delete_session(token)
    _clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=AuthResponse)
async def me(current_user: AuthUser = Depends(get_current_user)):
    return AuthResponse(user=current_user)


@router.get("/users", response_model=list[AuthUser])
async def list_users(_: AuthUser = Depends(require_admin_user)):
    return get_auth_service().list_users()


@router.post("/users", response_model=AuthUser)
async def create_user(
    request: CreateUserRequest,
    _: AuthUser = Depends(require_admin_user),
):
    try:
        return get_auth_service().create_user(request.username, request.password, request.role)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.patch("/users/{user_id}", response_model=AuthUser)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: AuthUser = Depends(require_admin_user),
):
    auth_service = get_auth_service()
    if current_user.user_id == user_id and request.is_active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate your own account")
    if current_user.user_id == user_id and request.role and request.role != "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove your own admin role")

    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    would_remove_active_admin = (
        target_user.role == "admin"
        and target_user.is_active
        and (
            (request.role is not None and request.role != "admin")
            or request.is_active is False
        )
    )
    if would_remove_active_admin and auth_service.count_active_admins() <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove the last active admin")

    try:
        return auth_service.update_user(
            user_id=user_id,
            role=request.role,
            is_active=request.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


__all__ = ["router"]
