"""
Health API Router
健康檢查 API
"""

import sys
from pathlib import Path

import httpx
from fastapi import APIRouter

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from services.processing_service import get_processing_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康檢查，包含 LLM 狀態"""
    # 檢查 Ollama LLM 狀態 (支援遠端 API) - 使用 async HTTP
    llm_status = "offline"
    llm_model = OLLAMA_MODEL  # 使用配置的模型
    ollama_url = OLLAMA_BASE_URL.rstrip("/")
    available_models: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                available_models = [m["name"] for m in data.get("models", [])]
                
                # 檢查配置的模型是否可用
                if OLLAMA_MODEL in available_models:
                    llm_status = "online"
                elif available_models:
                    llm_status = "model_not_found"
    except httpx.TimeoutException:
        llm_status = "timeout"
    except Exception:
        pass

    # 檢查引擎狀態
    processing_service = get_processing_service()
    engine_available = processing_service.engine_available

    return {
        "status": "healthy",
        "llm": {
            "status": llm_status,
            "model": llm_model,
            "provider": "ollama",
            "endpoint": ollama_url,
            "available_models": available_models[:5] if available_models else [],  # 最多顯示 5 個
        },
        "engine_available": engine_available,
    }
