"""
LLM Configuration Service
LLM 設定服務 - 管理 LLM 連線設定
"""

import json
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM 設定模型"""

    provider: str = "ollama"  # ollama, openai, azure
    base_url: str = "http://localhost:11434"
    model: str = "gemma3:27b"
    api_key: str | None = None  # 用於 OpenAI/Azure
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120


class LLMModel(BaseModel):
    """LLM 模型資訊"""

    name: str
    size: str | None = None
    modified_at: str | None = None
    quantization: str | None = None


class LLMStatus(BaseModel):
    """LLM 狀態"""

    online: bool = False
    provider: str = "ollama"
    endpoint: str = ""
    current_model: str | None = None
    available_models: list[LLMModel] = []
    error: str | None = None


class LLMConfigService:
    """LLM 設定服務"""

    def __init__(self) -> None:
        self._config_dir = Path(__file__).parent.parent / "data" / "llm_configs"
        self._config_file = self._config_dir / "config.json"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()

    def _load_config(self) -> LLMConfig:
        """載入設定"""
        if self._config_file.exists():
            try:
                with open(self._config_file, encoding="utf-8") as f:
                    data = json.load(f)
                return LLMConfig(**data)
            except Exception:
                pass

        # 從環境變數載入預設值（預設使用外部 Ollama 服務）
        return LLMConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://192.168.1.2:30133"),
            model=os.getenv("OLLAMA_MODEL", "gemma3:27b"),
        )

    def _save_config(self) -> None:
        """儲存設定"""
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.model_dump(), f, ensure_ascii=False, indent=2)

    def get_config(self) -> LLMConfig:
        """取得目前設定"""
        return self._config

    def update_config(self, config: LLMConfig) -> LLMConfig:
        """更新設定"""
        self._config = config
        self._save_config()
        return self._config

    def update_partial(self, **kwargs: Any) -> LLMConfig:
        """部分更新設定"""
        current = self._config.model_dump()
        current.update(kwargs)
        self._config = LLMConfig(**current)
        self._save_config()
        return self._config

    async def get_status(self) -> LLMStatus:
        """取得 LLM 狀態"""
        status = LLMStatus(
            provider=self._config.provider,
            endpoint=self._config.base_url,
        )

        if self._config.provider == "ollama":
            status = await self._check_ollama_status(status)
        elif self._config.provider == "openai":
            status = await self._check_openai_status(status)

        return status

    async def _check_ollama_status(self, status: LLMStatus) -> LLMStatus:
        """檢查 Ollama 狀態"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._config.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    status.online = True
                    status.available_models = [
                        LLMModel(
                            name=m.get("name", ""),
                            size=self._format_size(m.get("size", 0)),
                            modified_at=m.get("modified_at"),
                            quantization=m.get("details", {}).get("quantization_level"),
                        )
                        for m in models
                    ]

                    # 檢查目前選擇的模型是否可用
                    model_names = [m.name for m in status.available_models]
                    if self._config.model in model_names:
                        status.current_model = self._config.model
                    elif model_names:
                        status.current_model = model_names[0]
        except httpx.TimeoutException:
            status.error = "連線超時"
        except httpx.ConnectError:
            status.error = "無法連線到 Ollama 服務"
        except Exception as e:
            status.error = str(e)

        return status

    async def _check_openai_status(self, status: LLMStatus) -> LLMStatus:
        """檢查 OpenAI 狀態"""
        if not self._config.api_key:
            status.error = "未設定 API Key"
            return status

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])

                    status.online = True
                    status.available_models = [
                        LLMModel(name=m.get("id", ""))
                        for m in models
                        if "gpt" in m.get("id", "").lower()
                    ]
                    status.current_model = self._config.model
                else:
                    status.error = f"API 錯誤: {response.status_code}"
        except Exception as e:
            status.error = str(e)

        return status

    def _format_size(self, size_bytes: int) -> str:
        """格式化檔案大小"""
        if size_bytes == 0:
            return "Unknown"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    async def list_models(self) -> list[LLMModel]:
        """列出可用的模型"""
        status = await self.get_status()
        return status.available_models

    async def set_model(self, model_name: str) -> LLMConfig:
        """設定使用的模型"""
        status = await self.get_status()
        model_names = [m.name for m in status.available_models]

        if model_name not in model_names:
            raise ValueError(f"模型 '{model_name}' 不可用。可用模型: {model_names}")

        return self.update_partial(model=model_name)

    async def test_connection(self) -> dict[str, Any]:
        """測試 LLM 連線"""
        status = await self.get_status()

        if not status.online:
            return {
                "success": False,
                "error": status.error or "無法連線",
                "provider": self._config.provider,
                "endpoint": self._config.base_url,
            }

        # 嘗試簡單的生成測試
        if self._config.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._config.base_url}/api/generate",
                        json={
                            "model": status.current_model or self._config.model,
                            "prompt": "Say 'OK' if you can understand this.",
                            "stream": False,
                        },
                    )

                    if response.status_code == 200:
                        return {
                            "success": True,
                            "provider": self._config.provider,
                            "model": status.current_model,
                            "response_preview": response.json().get("response", "")[:100],
                        }
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "success": status.online,
            "provider": self._config.provider,
            "model": status.current_model,
        }


# Singleton instance
_llm_config_service: LLMConfigService | None = None


def get_llm_config_service() -> LLMConfigService:
    """取得 LLMConfigService singleton"""
    global _llm_config_service
    if _llm_config_service is None:
        _llm_config_service = LLMConfigService()
    return _llm_config_service
