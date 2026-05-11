"""
Medical De-identification Web API
FastAPI 後端服務 (模組化版本)

這是精簡後的入口檔案，所有業務邏輯已移至模組化結構：
- api/: API 路由
- models/: Pydantic 資料模型
- services/: 業務邏輯服務
- config.py: 應用配置
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# 確保 backend 目錄在 path 中
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from api import api_router
from config import (
    AUTH_MODE,
    CORS_ORIGINS,
    RESULT_TTL_HOURS,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    UPLOAD_TTL_HOURS,
    ensure_directories,
)
from logging_config import configure_logging
from security import has_valid_service_token, validate_browser_origin
from services.auth_service import get_auth_service
from services.file_service import get_file_service
from services.processing_service import get_processing_service
from services.task_service import get_task_service

# 配置 structured logging。預設 INFO，避免生產環境寫入 PHI debug 片段。
configure_logging(json_output=True, console_output=True)
ANONYMOUS_SESSION_SKIP_PATHS = {
    "/api/auth/bootstrap",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/setup-required",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    ensure_directories()
    if "*" in CORS_ORIGINS:
        raise RuntimeError("CORS wildcard is not allowed when credentials are enabled")
    logger.info("🚀 Medical De-identification API started")
    logger.info("📁 Data directories initialized")
    logger.info("Allowed CORS origins configured", origins=CORS_ORIGINS)
    get_file_service().cleanup_stale_uploads(UPLOAD_TTL_HOURS)
    get_task_service().mark_interrupted_tasks_failed()
    get_processing_service().cleanup_expired_outputs(RESULT_TTL_HOURS)

    yield

    # 關閉時
    logger.info("👋 Medical De-identification API stopped")


app = FastAPI(
    title="Medical De-identification API",
    description="醫療文本去識別化 Web API",
    version="2.0.0",  # 版本升級
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def anonymous_session_middleware(request: Request, call_next):
    """Issue an HttpOnly per-browser session when password auth is disabled."""
    token_to_set = None
    expires_at = None
    if (
        AUTH_MODE == "anonymous_session"
        and request.method.upper() != "OPTIONS"
        and request.url.path.startswith("/api/")
        and request.url.path not in ANONYMOUS_SESSION_SKIP_PATHS
        and not has_valid_service_token(
            request.headers.get("authorization"),
            request.headers.get("x-api-key"),
        )
    ):
        try:
            validate_browser_origin(
                request,
                authorization=request.headers.get("authorization"),
                x_api_key=request.headers.get("x-api-key"),
            )
        except Exception as exc:
            status_code = getattr(exc, "status_code", 403)
            detail = getattr(exc, "detail", "Invalid request origin")
            return JSONResponse(status_code=status_code, content={"detail": detail})

        auth_service = get_auth_service()
        token = request.cookies.get(SESSION_COOKIE_NAME)
        user = auth_service.get_user_by_session(token) if token else None
        if user is None:
            user, token_to_set, expires_at = auth_service.create_anonymous_session()
        request.state.user = user

    response = await call_next(request)
    if token_to_set and expires_at:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token_to_set,
            expires=expires_at,
            httponly=True,
            secure=SESSION_COOKIE_SECURE,
            samesite=SESSION_COOKIE_SAMESITE,
            path="/",
        )
    return response


# 註冊 API 路由
app.include_router(api_router)


# ============================================================
# 入口點
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("MEDICAL_DEID_BACKEND_HOST", "127.0.0.1"),
        port=8000,
        reload=True,
    )
