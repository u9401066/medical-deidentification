"""
PHI Configuration Models
PHI 配置資料模型
"""
from pydantic import BaseModel, Field


class PHITypeConfig(BaseModel):
    """單一 PHI 類型配置"""
    enabled: bool = True
    masking: str = "mask"  # mask, hash, replace, delete, keep
    replace_with: str | None = None  # 自訂替換詞，當 masking 為 'replace' 時使用


class PHIConfig(BaseModel):
    """PHI 處理配置"""
    masking_type: str = Field(default="redact", description="redact, hash, pseudonymize")
    phi_types: list[str] | dict[str, PHITypeConfig] = Field(default_factory=lambda: [
        "NAME", "DATE", "PHONE", "EMAIL", "ADDRESS", "ID_NUMBER", "MEDICAL_RECORD"
    ])
    preserve_format: bool = Field(default=True)
    custom_patterns: dict[str, str] | None = None
    
    def get_enabled_types(self) -> list[str]:
        """取得啟用的 PHI 類型列表"""
        if isinstance(self.phi_types, list):
            return self.phi_types
        return [k for k, v in self.phi_types.items() if v.enabled]
    
    def get_replace_text(self, phi_type: str) -> str | None:
        """取得指定 PHI 類型的替換詞"""
        if isinstance(self.phi_types, dict):
            config = self.phi_types.get(phi_type)
            if config and config.masking == "replace":
                return config.replace_with or f"[{phi_type}]"
        return None


__all__ = ["PHIConfig", "PHITypeConfig"]
