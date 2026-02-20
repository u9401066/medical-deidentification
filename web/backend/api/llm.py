"""
LLM API Router
LLM 設定與狀態 API
"""

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from services.llm_config_service import LLMConfig, get_llm_config_service

router = APIRouter()


# === 請求模型 ===


class LLMConfigUpdateRequest(BaseModel):
    """LLM 設定更新請求"""

    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: int | None = None


class SetModelRequest(BaseModel):
    """設定模型請求"""

    model: str


# === LLM 狀態 ===


@router.get("/llm/status")
async def get_llm_status() -> dict[str, Any]:
    """取得 LLM 狀態 (連線狀態、可用模型)"""
    service = get_llm_config_service()
    status = await service.get_status()
    return status.model_dump()


@router.get("/llm/models")
async def list_llm_models() -> list[dict[str, Any]]:
    """列出可用的 LLM 模型"""
    service = get_llm_config_service()
    models = await service.list_models()
    return [m.model_dump() for m in models]


@router.post("/llm/test")
async def test_llm_connection() -> dict[str, Any]:
    """測試 LLM 連線"""
    service = get_llm_config_service()
    return await service.test_connection()


# === LLM 設定 ===


@router.get("/llm/config")
async def get_llm_config() -> dict[str, Any]:
    """取得目前的 LLM 設定"""
    service = get_llm_config_service()
    config = service.get_config()
    # 隱藏 API Key
    result = config.model_dump()
    if result.get("api_key"):
        result["api_key"] = "***" + result["api_key"][-4:] if len(result["api_key"]) > 4 else "***"
    return result


@router.put("/llm/config")
async def update_llm_config(request: LLMConfigUpdateRequest) -> dict[str, Any]:
    """更新 LLM 設定"""
    service = get_llm_config_service()

    # 過濾掉 None 值
    updates = {k: v for k, v in request.model_dump().items() if v is not None}

    if not updates:
        raise HTTPException(400, "未提供任何更新內容")

    updated = service.update_partial(**updates)

    result = updated.model_dump()
    if result.get("api_key"):
        result["api_key"] = "***"

    return {"message": "設定已更新", "config": result}


@router.post("/llm/config/reset")
async def reset_llm_config() -> dict[str, Any]:
    """重置 LLM 設定為預設值"""
    service = get_llm_config_service()
    default_config = LLMConfig()
    updated = service.update_config(default_config)
    return {"message": "設定已重置", "config": updated.model_dump()}


# === 模型選擇 ===


@router.post("/llm/model")
async def set_llm_model(request: SetModelRequest) -> dict[str, Any]:
    """設定使用的 LLM 模型"""
    service = get_llm_config_service()
    try:
        updated = await service.set_model(request.model)
        return {"message": f"已切換至模型: {request.model}", "config": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# === 支援的提供者 ===


@router.get("/llm/providers")
async def list_llm_providers() -> list[dict[str, Any]]:
    """列出支援的 LLM 提供者"""
    return [
        {
            "id": "ollama",
            "name": "Ollama",
            "description": "本地或遠端 Ollama 服務",
            "requires_api_key": False,
            "default_url": "http://localhost:11434",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "OpenAI GPT 模型 (需要 API Key)",
            "requires_api_key": True,
            "default_url": "https://api.openai.com",
        },
        {
            "id": "azure",
            "name": "Azure OpenAI",
            "description": "Azure OpenAI 服務 (需要 API Key)",
            "requires_api_key": True,
            "default_url": "",
        },
    ]
