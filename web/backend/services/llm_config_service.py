"""
LLM Configuration Service
LLM 設定服務 - 管理 LLM 連線設定
"""

import json
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from config import DATA_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL


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
        self._config_dir = DATA_DIR / "llm_configs"
        self._config_file = self._config_dir / "config.json"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()

    def _default_config(self) -> LLMConfig:
        return LLMConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
            model=os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
        )

    def _load_config(self) -> LLMConfig:
        """載入設定"""
        if self._config_file.exists():
            try:
                with open(self._config_file, encoding="utf-8") as f:
                    data = json.load(f)
                config = LLMConfig(**data)
                self._validate_base_url(config.base_url)
                return config
            except Exception:
                return self._default_config()

        # 從環境變數載入預設值（預設使用外部 Ollama 服務）
        return self._default_config()

    def _save_config(self) -> None:
        """儲存設定"""
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.model_dump(), f, ensure_ascii=False, indent=2)

    def _validate_base_url(self, base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("LLM base_url must be an http(s) URL")
        if parsed.username or parsed.password:
            raise ValueError("LLM base_url must not include credentials")

        allowed_hosts = {
            host.strip().lower()
            for host in os.getenv("MEDICAL_DEID_ALLOWED_LLM_HOSTS", "").split(",")
            if host.strip()
        }
        # Safe default: only the configured deployment endpoint and localhost.
        default_host = urlparse(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).hostname
        if not allowed_hosts:
            allowed_hosts = {"localhost", "127.0.0.1", "::1"}
            if default_host:
                allowed_hosts.add(default_host.lower())

        if parsed.hostname.lower() not in allowed_hosts:
            raise ValueError(
                "LLM endpoint host is not allowed. Set MEDICAL_DEID_ALLOWED_LLM_HOSTS to permit it."
            )

    def get_config(self) -> LLMConfig:
        """取得目前設定"""
        return self._config

    def update_config(self, config: LLMConfig) -> LLMConfig:
        """更新設定"""
        self._validate_base_url(config.base_url)
        self._config = config
        self._save_config()
        return self._config

    def reset_to_default(self) -> LLMConfig:
        """Reset to deployment defaults from environment/config."""
        self._config = self._default_config()
        self._save_config()
        return self._config

    def update_partial(self, **kwargs: Any) -> LLMConfig:
        """部分更新設定"""
        current = self._config.model_dump()
        current.update(kwargs)
        if "base_url" in kwargs:
            self._validate_base_url(str(kwargs["base_url"]))
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
