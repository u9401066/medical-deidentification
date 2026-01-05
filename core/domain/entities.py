"""
Domain Entities | 領域實體

Core entities for medical document de-identification.
醫療文件去識別化的核心實體。
"""

from dataclasses import dataclass

from .phi_types import CustomPHIType, PHIType


@dataclass(frozen=True)
class PHIEntity:
    """
    PHI Entity Value Object | PHI 實體值物件
    
    Represents a detected piece of Protected Health Information.
    表示檢測到的個人健康資訊片段。
    
    Supports both standard PHIType enum and custom types discovered from regulations.
    同時支援標準 PHIType enum 和從法規中發現的自定義類型。
    """

    type: PHIType  # Standard PHI type (use PHIType.CUSTOM for custom types)
    text: str  # The actual PHI text detected
    start_pos: int  # Start position in document
    end_pos: int  # End position in document
    confidence: float  # Detection confidence (0.0-1.0)
    reason: str = ""  # Why this is considered PHI according to regulations
    regulation_source: str | None = None  # Which regulation rule detected it
    custom_type: CustomPHIType | None = None  # Custom PHI type if applicable

    def __post_init__(self) -> None:
        """Validate invariants | 驗證不變量"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.start_pos < 0 or self.end_pos < self.start_pos:
            raise ValueError("Invalid position range")
        if self.type == PHIType.CUSTOM and self.custom_type is None:
            raise ValueError("custom_type must be provided when type is CUSTOM")

    def get_type_name(self) -> str:
        """
        Get the display name of this PHI type | 獲取此 PHI 類型的顯示名稱
        
        Returns:
            Standard type name or custom type name
        """
        if self.type == PHIType.CUSTOM and self.custom_type:
            return self.custom_type.name
        return self.type.value

    def get_full_description(self) -> str:
        """
        Get full description of this PHI entity | 獲取此 PHI 實體的完整描述
        
        Returns:
            Detailed description including type and regulation source
        """
        base = f"{self.get_type_name()}: {self.text}"
        if self.custom_type:
            base += f" ({self.custom_type.description})"
        if self.regulation_source:
            base += f" [Source: {self.regulation_source}]"
        return base

    def is_high_risk(self) -> bool:
        """
        Check if this PHI entity is high-risk for identification | 檢查是否為高識別風險
        
        High-risk includes: rare diseases, age >90, specific facilities, etc.
        高風險包括: 罕見疾病、年齡>90、特定醫療機構等。
        """
        high_risk_types = [
            PHIType.RARE_DISEASE,
            PHIType.AGE_OVER_90,
            PHIType.BIOMETRIC,
            PHIType.GENETIC_INFO,
            PHIType.SSN,
        ]

        if self.type in high_risk_types:
            return True

        # Check custom type risk
        if self.custom_type and self.custom_type.is_high_risk:
            return True

        return False
