"""Authentication and authorization helpers."""

import secrets
from urllib.parse import urlparse

from config import API_TOKEN, AUTH_MODE, BACKEND_HOST, CORS_ORIGINS, SESSION_COOKIE_NAME
from fastapi import Header, HTTPException, Request, status
from models.auth import AuthUser
from services.auth_service import get_auth_service

PUBLIC_PATHS = {
    "/api/live",
    "/api/ready",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/bootstrap",
    "/api/auth/setup-required",
}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SYSTEM_ADMIN = AuthUser(user_id="system", username="system", role="admin", is_active=True)


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS


def _origin_base(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_trusted_frontend_proxy(request: Request) -> bool:
    forwarded_by_frontend = request.headers.get("x-medical-deid-frontend-proxy") == "1"
    if not forwarded_by_frontend:
        return False

    client_host = request.client.host if request.client else ""
    if client_host in {"127.0.0.1", "::1", "localhost"}:
        return True

    # Uvicorn may rewrite request.client from X-Forwarded-For when the local
    # frontend proxy forwards a LAN browser request. If the backend itself is
    # loopback-bound, only local processes can reach it, so the proxy marker is
    # still trustworthy even though request.client now shows the browser IP.
    return BACKEND_HOST in {"127.0.0.1", "::1", "localhost"} and bool(
        request.headers.get("x-forwarded-host")
    )


def validate_browser_origin(
    request: Request,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> None:
    """Block cross-site unsafe browser requests that would otherwise carry cookies."""
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-site API request blocked",
        )
    if request.method.upper() not in UNSAFE_METHODS:
        return
    if _is_trusted_frontend_proxy(request):
        return
    if _service_token_user(authorization=authorization, x_api_key=x_api_key) is not None:
        return

    raw_origin = request.headers.get("origin")
    raw_referer = request.headers.get("referer")
    if raw_origin == "null":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )

    origin = _origin_base(raw_origin)
    referer = _origin_base(raw_referer)
    browser_origin = origin or referer
    if not browser_origin:
        if request.cookies.get(SESSION_COOKIE_NAME):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing request origin",
            )
        return

    allowed_origins = {_origin_base(value) for value in CORS_ORIGINS}
    allowed_origins.discard(None)
    if browser_origin not in allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )


def _service_token_user(
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> AuthUser | None:
    if not API_TOKEN:
        return None

    bearer_prefix = "Bearer "
    token = x_api_key
    if authorization and authorization.startswith(bearer_prefix):
        token = authorization[len(bearer_prefix):]

    if token and secrets.compare_digest(token, API_TOKEN):
        return SYSTEM_ADMIN
    return None


def has_valid_service_token(authorization: str | None, x_api_key: str | None) -> bool:
    """Return true when the request carries the configured machine-to-machine token."""
    return _service_token_user(authorization=authorization, x_api_key=x_api_key) is not None


def _session_user(request: Request, authorization: str | None = None) -> AuthUser | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    bearer_prefix = "Bearer "
    if not token and authorization and authorization.startswith(bearer_prefix):
        maybe_token = authorization[len(bearer_prefix):]
        if not API_TOKEN or not secrets.compare_digest(maybe_token, API_TOKEN):
            token = maybe_token
    if not token:
        return None
    return get_auth_service().get_user_by_session(token)


async def require_authenticated_request(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Global guard for API routes."""
    validate_browser_origin(request, authorization=authorization, x_api_key=x_api_key)
    if _is_public_path(request.url.path):
        return

    existing_user = getattr(request.state, "user", None)
    if existing_user is not None:
        return

    user = _service_token_user(authorization=authorization, x_api_key=x_api_key)
    if user is None:
        user = _session_user(request, authorization=authorization)

    if user is not None:
        request.state.user = user
        return

    if AUTH_MODE == "anonymous_session":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Anonymous session required",
        )

    if get_auth_service().count_users() == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No admin user exists. Bootstrap the first admin account.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


async def get_current_user(request: Request) -> AuthUser:
    user = getattr(request.state, "user", None)
    if user is None:
        await require_authenticated_request(request)
        user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


async def require_admin_user(request: Request) -> AuthUser:
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user


__all__ = [
    "get_current_user",
    "has_valid_service_token",
    "require_admin_user",
    "require_authenticated_request",
    "validate_browser_origin",
]
