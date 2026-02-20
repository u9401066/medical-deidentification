"""
Health API Router
健康檢查 API
"""

import subprocess
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
    llm_config = llm_config_service.get_config()
    
    # 檢查 Ollama LLM 狀態 (支援遠端 API)
    llm_status = "offline"
    ollama_url = llm_config.base_url.rstrip("/")

    try:
        result = subprocess.run(
            ["curl", "-s", f"{ollama_url}/api/tags"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            import json

            try:
                data = json.loads(result.stdout)
                if data.get("models"):
                    llm_status = "online"
            except json.JSONDecodeError:
                pass
    except subprocess.TimeoutExpired:
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
            "model": llm_config.model,  # 使用設定中的模型
            "provider": llm_config.provider,
            "endpoint": ollama_url,
        },
        "engine_available": engine_available,
    }
