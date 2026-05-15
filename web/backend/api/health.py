"""
Health API Router
健康檢查 API
"""

import sys
from pathlib import Path

from fastapi import APIRouter

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
    llm_status_info = await llm_config_service.get_status()

    # 檢查引擎狀態
    processing_service = get_processing_service()
    engine_available = processing_service.engine_available

    return {
        "status": "healthy",
        "llm": {
            "status": "online" if llm_status_info.online else "offline",
            "model": llm_status_info.current_model,  # 確認實際可用模型
            "configured_model": llm_config_service.get_config().model,
            "provider": llm_status_info.provider,
            "endpoint": llm_status_info.endpoint,
        },
        "engine_available": engine_available,
    }
