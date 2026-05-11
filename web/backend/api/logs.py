"""
Frontend Logs API Router
前端錯誤日誌接收 API
"""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel

from config import LOG_DIR
from models.auth import AuthUser
from security import require_admin_user

router = APIRouter(prefix="/logs", tags=["logs"])

# 日誌檔案路徑
FRONTEND_ERROR_LOG = LOG_DIR / "frontend-errors.jsonl"
REDACTED = "[REDACTED]"


class FrontendError(BaseModel):
    message: str
    stack: str | None = None
    componentStack: str | None = None
    url: str
    userAgent: str
    timestamp: str
    type: str
    extra: dict[str, Any] | None = None


class FrontendErrorsRequest(BaseModel):
    errors: list[FrontendError]


def _sanitize_extra(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_extra(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_extra(item) for item in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return REDACTED


def _sanitize_error(error: FrontendError) -> dict[str, Any]:
    data = error.model_dump()
    # Frontend exception strings can contain API bodies or rendered PHI.
    data["message"] = REDACTED
    data["stack"] = None
    data["componentStack"] = None
    data["extra"] = _sanitize_extra(data.get("extra"))
    return data


@router.post("/frontend-errors")
async def receive_frontend_errors(request: FrontendErrorsRequest):
    """接收前端錯誤日誌"""
    FRONTEND_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)

    received_at = datetime.now().isoformat()

    with open(FRONTEND_ERROR_LOG, "a", encoding="utf-8") as f:
        for error in request.errors:
            log_entry = {
                "received_at": received_at,
                **_sanitize_error(error),
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            # 同時輸出到後端日誌
            logger.warning(
                "Frontend error received",
                frontend_error_type=error.type,
                url=error.url,
            )

    return {
        "status": "ok",
        "received": len(request.errors),
    }


@router.get("/frontend-errors")
async def get_frontend_errors(
    limit: int = 50,
    _: AuthUser = Depends(require_admin_user),
):
    """取得最近的前端錯誤（供 debug 用）"""
    if not FRONTEND_ERROR_LOG.exists():
        return {"errors": [], "total": 0}

    errors = []
    with open(FRONTEND_ERROR_LOG, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # 返回最新的 N 筆
    recent = errors[-limit:] if len(errors) > limit else errors
    recent.reverse()  # 最新的在前

    return {
        "errors": recent,
        "total": len(errors),
    }


@router.delete("/frontend-errors")
async def clear_frontend_errors(_: AuthUser = Depends(require_admin_user)):
    """清空前端錯誤日誌"""
    if FRONTEND_ERROR_LOG.exists():
        FRONTEND_ERROR_LOG.unlink()
    return {"status": "cleared"}
