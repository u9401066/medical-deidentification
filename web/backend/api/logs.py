"""
Frontend Logs API Router
前端錯誤日誌接收 API
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/logs", tags=["logs"])

# 日誌檔案路徑
FRONTEND_ERROR_LOG = Path(__file__).parent.parent.parent.parent / "logs" / "frontend-errors.jsonl"


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


@router.post("/frontend-errors")
async def receive_frontend_errors(request: FrontendErrorsRequest):
    """接收前端錯誤日誌"""
    FRONTEND_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    received_at = datetime.now().isoformat()
    
    with open(FRONTEND_ERROR_LOG, "a", encoding="utf-8") as f:
        for error in request.errors:
            log_entry = {
                "received_at": received_at,
                **error.model_dump(),
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            # 同時輸出到後端日誌
            logger.warning(
                f"[Frontend {error.type}] {error.message} | URL: {error.url}"
            )
    
    return {
        "status": "ok",
        "received": len(request.errors),
    }


@router.get("/frontend-errors")
async def get_frontend_errors(limit: int = 50):
    """取得最近的前端錯誤（供 debug 用）"""
    if not FRONTEND_ERROR_LOG.exists():
        return {"errors": [], "total": 0}
    
    errors = []
    with open(FRONTEND_ERROR_LOG, "r", encoding="utf-8") as f:
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
async def clear_frontend_errors():
    """清空前端錯誤日誌"""
    if FRONTEND_ERROR_LOG.exists():
        FRONTEND_ERROR_LOG.unlink()
    return {"status": "cleared"}
