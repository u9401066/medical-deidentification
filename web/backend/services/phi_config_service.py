"""
PHI Configuration Service
PHI 類型設定服務 - 獨立管理 PHI 設定的持久化與導入導出
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import DATA_DIR
from models.config import PHIConfig, PHITypeConfig

# 設定檔路徑
PHI_CONFIG_DIR = DATA_DIR / "phi_configs"
DEFAULT_CONFIG_FILE = PHI_CONFIG_DIR / "current_config.json"
PRESETS_DIR = PHI_CONFIG_DIR / "presets"


class PHIConfigService:
    """PHI 設定服務 - 管理 PHI 類型設定的持久化、導入與導出"""

    def __init__(self) -> None:
        self._ensure_directories()
        self._config: PHIConfig | None = None
        self._load_config()

    def _ensure_directories(self) -> None:
        """確保設定目錄存在"""
        PHI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)

        # 建立預設 preset 如果不存在
        self._create_default_presets()

    def _create_default_presets(self) -> None:
        """建立預設的設定範本"""
        presets = {
            "hipaa_standard": {
                "name": "HIPAA 標準",
                "description": "符合 HIPAA Safe Harbor 的 18 項識別符標準配置",
                "config": {
                    "masking_type": "redact",
                    "preserve_format": True,
                    "phi_types": {
                        "NAME": {"enabled": True, "masking": "mask"},
                        "DATE": {"enabled": True, "masking": "mask"},
                        "PHONE": {"enabled": True, "masking": "mask"},
                        "FAX": {"enabled": True, "masking": "mask"},
                        "EMAIL": {"enabled": True, "masking": "mask"},
                        "SSN": {"enabled": True, "masking": "mask"},
                        "MEDICAL_RECORD": {"enabled": True, "masking": "mask"},
                        "ID_NUMBER": {"enabled": True, "masking": "mask"},
                        "ACCOUNT": {"enabled": True, "masking": "mask"},
                        "LICENSE": {"enabled": True, "masking": "mask"},
                        "VEHICLE": {"enabled": True, "masking": "mask"},
                        "DEVICE": {"enabled": True, "masking": "mask"},
                        "URL": {"enabled": True, "masking": "mask"},
                        "IP": {"enabled": True, "masking": "mask"},
                        "BIOMETRIC": {"enabled": True, "masking": "mask"},
                        "PHOTO": {"enabled": True, "masking": "mask"},
                        "AGE_OVER_89": {"enabled": True, "masking": "mask"},
                        "ADDRESS": {"enabled": True, "masking": "mask"},
                        "LOCATION": {"enabled": True, "masking": "mask"},
                    },
                },
            },
            "minimal": {
                "name": "最小化處理",
                "description": "僅處理最敏感的個人識別資訊",
                "config": {
                    "masking_type": "redact",
                    "preserve_format": True,
                    "phi_types": {
                        "NAME": {"enabled": True, "masking": "mask"},
                        "ID_NUMBER": {"enabled": True, "masking": "mask"},
                        "SSN": {"enabled": True, "masking": "mask"},
                        "MEDICAL_RECORD": {"enabled": True, "masking": "mask"},
                    },
                },
            },
            "research_safe": {
                "name": "研究安全模式",
                "description": "保留日期但移除直接識別符，適合研究用途",
                "config": {
                    "masking_type": "pseudonymize",
                    "preserve_format": True,
                    "phi_types": {
                        "NAME": {"enabled": True, "masking": "hash"},
                        "DATE": {"enabled": False, "masking": "keep"},
                        "PHONE": {"enabled": True, "masking": "mask"},
                        "EMAIL": {"enabled": True, "masking": "hash"},
                        "ADDRESS": {"enabled": True, "masking": "mask"},
                        "ID_NUMBER": {"enabled": True, "masking": "hash"},
                        "MEDICAL_RECORD": {"enabled": True, "masking": "hash"},
                    },
                },
            },
        }

        for preset_id, preset_data in presets.items():
            preset_file = PRESETS_DIR / f"{preset_id}.json"
            if not preset_file.exists():
                with open(preset_file, "w", encoding="utf-8") as f:
                    json.dump(preset_data, f, ensure_ascii=False, indent=2)
                logger.info(f"📋 Created preset: {preset_id}")

    def _load_config(self) -> None:
        """載入目前的設定"""
        if DEFAULT_CONFIG_FILE.exists():
            try:
                with open(DEFAULT_CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                self._config = PHIConfig(**data)
                logger.info("📋 Loaded PHI config from file")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                self._config = PHIConfig()
        else:
            self._config = PHIConfig()

    def _save_config(self) -> None:
        """儲存目前的設定"""
        if self._config:
            with open(DEFAULT_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config.model_dump(), f, ensure_ascii=False, indent=2)
            logger.info("💾 Saved PHI config to file")

    # === 基本操作 ===

    def get_config(self) -> PHIConfig:
        """取得目前的 PHI 設定"""
        if self._config is None:
            self._config = PHIConfig()
        return self._config

    def update_config(self, config: PHIConfig) -> PHIConfig:
        """更新 PHI 設定"""
        self._config = config
        self._save_config()
        logger.info("✅ PHI config updated")
        return self._config

    def reset_to_default(self) -> PHIConfig:
        """重置為預設設定
        
        Returns:
            預設的 PHIConfig
        """
        self._config = PHIConfig()
        self._save_config()
        logger.warning("🔄 PHI config reset to defaults")
        return self._config

    def get_default_config(self) -> PHIConfig:
        """取得預設設定 (不影響目前設定)"""
        return PHIConfig()

    def get_phi_type_config(self, phi_type: str) -> PHITypeConfig | None:
        """取得單一 PHI 類型的設定"""
        config = self.get_config()
        if isinstance(config.phi_types, dict):
            return config.phi_types.get(phi_type)
        return None

    def update_phi_type_config(
        self,
        phi_type: str,
        enabled: bool | None = None,
        masking: str | None = None,
        replace_with: str | None = None,
    ) -> PHITypeConfig:
        """更新單一 PHI 類型的設定"""
        config = self.get_config()

        # 確保 phi_types 是 dict 格式
        if isinstance(config.phi_types, list):
            config.phi_types = {
                t: PHITypeConfig(enabled=True, masking="mask") for t in config.phi_types
            }

        # 取得或建立設定
        type_config = config.phi_types.get(phi_type, PHITypeConfig())

        # 更新設定
        if enabled is not None:
            type_config.enabled = enabled
        if masking is not None:
            type_config.masking = masking
        if replace_with is not None:
            type_config.replace_with = replace_with

        config.phi_types[phi_type] = type_config
        self._config = config
        self._save_config()

        return type_config

    # === 導入/導出 ===

    def export_config(self, include_metadata: bool = True) -> dict[str, Any]:
        """
        導出目前的設定為 JSON 格式

        Args:
            include_metadata: 是否包含匯出時間等元資料

        Returns:
            可直接序列化為 JSON 的字典
        """
        config = self.get_config()
        export_data: dict[str, Any] = {
            "config": config.model_dump(),
        }

        if include_metadata:
            export_data["metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "format": "phi_config_v1",
            }

        return export_data

    def import_config(self, data: dict[str, Any], validate: bool = True) -> PHIConfig:
        """
        從 JSON 資料導入設定

        Args:
            data: 設定資料 (可以是完整的導出格式或僅 config 部分)
            validate: 是否驗證格式

        Returns:
            導入後的設定

        Raises:
            ValueError: 如果格式不正確
        """
        # 支援兩種格式: 完整導出格式 或 純 config
        config_data = data.get("config", data)

        if validate:
            # 驗證必要欄位
            if "phi_types" not in config_data and "masking_type" not in config_data:
                raise ValueError("Invalid config format: missing required fields")

        try:
            new_config = PHIConfig(**config_data)
            self._config = new_config
            self._save_config()
            logger.info("📥 PHI config imported successfully")
            return new_config
        except Exception as e:
            raise ValueError(f"Failed to parse config: {e}") from e

    def export_config_file(self) -> Path:
        """
        導出設定到檔案並返回檔案路徑

        Returns:
            導出的檔案路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = PHI_CONFIG_DIR / f"export_{timestamp}.json"

        export_data = self.export_config(include_metadata=True)
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📤 Exported config to: {export_file}")
        return export_file

    # === Preset 管理 ===

    def list_presets(self) -> list[dict[str, Any]]:
        """列出所有可用的 preset"""
        presets = []
        for preset_file in PRESETS_DIR.glob("*.json"):
            try:
                with open(preset_file, encoding="utf-8") as f:
                    data = json.load(f)
                presets.append(
                    {
                        "id": preset_file.stem,
                        "name": data.get("name", preset_file.stem),
                        "description": data.get("description", ""),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to load preset {preset_file}: {e}")
        return presets

    def get_preset(self, preset_id: str) -> dict[str, Any] | None:
        """取得指定的 preset"""
        preset_file = PRESETS_DIR / f"{preset_id}.json"
        if not preset_file.exists():
            return None

        with open(preset_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    def apply_preset(self, preset_id: str) -> PHIConfig:
        """套用指定的 preset"""
        preset = self.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset not found: {preset_id}")

        config_data = preset.get("config", {})
        return self.import_config(config_data, validate=False)

    def save_as_preset(self, preset_id: str, name: str, description: str = "") -> dict[str, Any]:
        """將目前設定儲存為 preset"""
        config = self.get_config()
        preset_data = {
            "name": name,
            "description": description,
            "config": config.model_dump(),
            "created_at": datetime.now().isoformat(),
        }

        preset_file = PRESETS_DIR / f"{preset_id}.json"
        with open(preset_file, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Saved preset: {preset_id}")
        return {"id": preset_id, "name": name, "description": description}

    def delete_preset(self, preset_id: str) -> bool:
        """刪除指定的 preset"""
        # 防止刪除內建 preset
        builtin_presets = {"hipaa_standard", "minimal", "research_safe"}
        if preset_id in builtin_presets:
            raise ValueError(f"Cannot delete built-in preset: {preset_id}")

        preset_file = PRESETS_DIR / f"{preset_id}.json"
        if preset_file.exists():
            preset_file.unlink()
            logger.info(f"🗑️ Deleted preset: {preset_id}")
            return True
        return False


# Singleton instance
_phi_config_service: PHIConfigService | None = None


def get_phi_config_service() -> PHIConfigService:
    """取得 PHI 設定服務的單例"""
    global _phi_config_service
    if _phi_config_service is None:
        _phi_config_service = PHIConfigService()
    return _phi_config_service


__all__ = ["PHIConfigService", "get_phi_config_service"]
