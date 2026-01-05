"""
Value Objects | 值物件

Value objects for medical document de-identification domain.
醫療文件去識別化領域的值物件。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

# Avoid circular imports by using TYPE_CHECKING
if TYPE_CHECKING:
    from .entities import PHIEntity
    from .phi_types import CustomPHIType, PHIType


class SupportedLanguage(str, Enum):
    """Supported Languages for De-identification | 支援的去識別化語言"""

    TRADITIONAL_CHINESE = "zh-TW"  # 繁體中文 (Traditional Chinese)
    SIMPLIFIED_CHINESE = "zh-CN"   # 简体中文 (Simplified Chinese)
    ENGLISH = "en"                 # English
    JAPANESE = "ja"                # 日本語 (Japanese)
    KOREAN = "ko"                  # 한국어 (Korean)
    SPANISH = "es"                 # Español (Spanish)
    FRENCH = "fr"                  # Français (French)
    GERMAN = "de"                  # Deutsch (German)
    THAI = "th"                    # ไทย (Thai)
    VIETNAMESE = "vi"              # Tiếng Việt (Vietnamese)

    @classmethod
    def get_default(cls) -> "SupportedLanguage":
        """Get default language | 獲取預設語言"""
        return cls.TRADITIONAL_CHINESE

    @classmethod
    def is_supported(cls, lang_code: str) -> bool:
        """Check if language is supported | 檢查語言是否支援"""
        return lang_code in [lang.value for lang in cls]


@dataclass
class RegulationContext:
    """
    Regulation Context Value Object | 法規上下文值物件
    
    Contains regulation rules retrieved from RAG for context-aware de-identification.
    包含從 RAG 檢索的法規規則,用於上下文感知的去識別化。
    """

    applicable_regulations: list[str]
    retrieved_rules: list[str]
    masking_instructions: list[str]
    required_phi_types: list["PHIType"] = field(default_factory=list)  # Required PHI types to detect
    custom_phi_types: list["CustomPHIType"] = field(default_factory=list)  # Custom types from regulations
    strictness_level: str = "standard"  # "standard" or "strict"

    def has_rules(self) -> bool:
        """Check if any rules were retrieved | 檢查是否有檢索到規則"""
        return len(self.retrieved_rules) > 0

    def get_all_phi_types(self) -> list["PHIType"]:
        """
        Get all PHI types to detect based on context | 根據上下文獲取所有要檢測的 PHI 類型
        
        Returns appropriate PHI types based on regulation requirements and strictness.
        根據法規要求和嚴格程度返回適當的 PHI 類型。
        """
        # Import here to avoid circular dependency
        from .phi_types import PHIType

        if self.required_phi_types:
            return self.required_phi_types

        if self.strictness_level == "strict":
            return PHIType.get_strict_types()

        return PHIType.get_standard_types()

    def requires_custom_types(self) -> bool:
        """Check if custom PHI types are required | 檢查是否需要自定義 PHI 類型"""
        return len(self.custom_phi_types) > 0


@dataclass
class DocumentMetadata:
    """Document Metadata | 文件元數據"""

    document_type: str
    source: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    language: SupportedLanguage = field(default_factory=SupportedLanguage.get_default)
    custom_fields: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Validation Result | 驗證結果
    
    Contains quality metrics and validation status.
    包含品質指標與驗證狀態。
    """

    is_valid: bool
    residual_phi_detected: list["PHIEntity"] = field(default_factory=list)
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    compliance_status: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
