"""
Health API Router
健康檢查 API
"""

import sys
from pathlib import Path

import httpx
from fastapi import APIRouter, Response, status

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from services.llm_config_service import get_llm_config_service
from services.processing_service import get_processing_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康檢查，包含 LLM 狀態"""
    # 取得 LLM 設定
    llm_config_service = get_llm_config_service()
    llm_config = llm_config_service.get_config()
    
    # 檢查 Ollama LLM 狀態 (支援遠端 API)
    llm_status = "offline"
    ollama_url = llm_config.base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            result = await client.get(f"{ollama_url}/api/tags")
            if result.status_code == 200 and result.json().get("models"):
                llm_status = "online"
    except httpx.TimeoutException:
        llm_status = "timeout"
    except Exception:
        llm_status = "offline"

    # 檢查引擎狀態
    processing_service = get_processing_service()
    engine_available = processing_service.engine_available

    return {
        "status": "healthy",
        "llm": {
            "status": llm_status,
            "model": llm_config.model,  # 使用設定中的模型
            "provider": llm_config.provider,
        },
        "engine_available": engine_available,
    }


@router.get("/live")
async def live_check():
    """Process liveness check."""
    return {"status": "alive"}


@router.get("/ready")
async def ready_check(response: Response):
    """Readiness check for monitoring/load balancers."""
    health = await health_check()
    ready = health["engine_available"] and health["llm"]["status"] == "online"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ready else "not_ready"}
