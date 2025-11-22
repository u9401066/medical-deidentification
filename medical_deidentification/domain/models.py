"""
Domain Models | 領域模型

Core domain entities and value objects for medical document de-identification.
醫療文件去識別化的核心領域實體與值物件。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


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


class PHIType(str, Enum):
    """Protected Health Information Types | 個人健康資訊類型"""
    
    NAME = "NAME"  # 姓名
    DATE = "DATE"  # 日期
    LOCATION = "LOCATION"  # 地點
    ID = "ID"  # 識別碼
    CONTACT = "CONTACT"  # 聯絡資訊
    AGE = "AGE"  # 年齡 (>89)
    BIOMETRIC = "BIOMETRIC"  # 生物特徵
    MEDICAL_RECORD_NUMBER = "MEDICAL_RECORD_NUMBER"  # 病歷號
    OTHER = "OTHER"  # 其他


@dataclass(frozen=True)
class PHIEntity:
    """
    PHI Entity Value Object | PHI 實體值物件
    
    Represents a detected piece of Protected Health Information.
    表示檢測到的個人健康資訊片段。
    """
    
    type: PHIType
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    regulation_source: Optional[str] = None  # Which regulation rule detected it
    
    def __post_init__(self) -> None:
        """Validate invariants | 驗證不變量"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.start_pos < 0 or self.end_pos < self.start_pos:
            raise ValueError("Invalid position range")


@dataclass
class RegulationContext:
    """
    Regulation Context Value Object | 法規上下文值物件
    
    Contains regulation rules retrieved from RAG for context-aware de-identification.
    包含從 RAG 檢索的法規規則,用於上下文感知的去識別化。
    """
    
    applicable_regulations: List[str]
    retrieved_rules: List[str]
    masking_instructions: List[str]
    
    def has_rules(self) -> bool:
        """Check if any rules were retrieved | 檢查是否有檢索到規則"""
        return len(self.retrieved_rules) > 0


@dataclass
class DocumentMetadata:
    """Document Metadata | 文件元數據"""
    
    document_type: str
    source: Optional[str] = None
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
    residual_phi_detected: List[PHIEntity]
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    compliance_status: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class MedicalDocument:
    """
    Medical Document Aggregate Root | 醫療文件聚合根
    
    Main aggregate for the de-identification domain.
    去識別化領域的主要聚合。
    """
    
    def __init__(
        self,
        original_text: str,
        metadata: Optional[DocumentMetadata] = None,
        document_id: Optional[UUID] = None,
    ):
        self.id: UUID = document_id or uuid4()
        self.original_text: str = original_text
        self.detected_entities: List[PHIEntity] = []
        self.deidentified_text: Optional[str] = None
        self.metadata: DocumentMetadata = metadata or DocumentMetadata(document_type="unknown")
        self.regulation_context: Optional[RegulationContext] = None
        self.validation_result: Optional[ValidationResult] = None
        self._created_at: datetime = datetime.now()
    
    def add_detected_entity(self, entity: PHIEntity) -> None:
        """
        Add a detected PHI entity | 添加檢測到的 PHI 實體
        
        Args:
            entity: The PHI entity to add
        """
        self.detected_entities.append(entity)
    
    def set_regulation_context(self, context: RegulationContext) -> None:
        """
        Set the regulation context from RAG | 設置來自 RAG 的法規上下文
        
        Args:
            context: Regulation context with retrieved rules
        """
        self.regulation_context = context
    
    def apply_deidentification(self, deidentified_text: str) -> None:
        """
        Apply de-identified text | 應用去識別化文本
        
        Args:
            deidentified_text: The de-identified version of the text
        """
        if not deidentified_text:
            raise ValueError("De-identified text cannot be empty")
        self.deidentified_text = deidentified_text
    
    def set_validation_result(self, result: ValidationResult) -> None:
        """
        Set validation result | 設置驗證結果
        
        Args:
            result: Validation result with quality metrics
        """
        self.validation_result = result
    
    def is_deidentified(self) -> bool:
        """Check if document has been de-identified | 檢查文件是否已去識別化"""
        return self.deidentified_text is not None
    
    def is_validated(self) -> bool:
        """Check if document has been validated | 檢查文件是否已驗證"""
        return self.validation_result is not None and self.validation_result.is_valid
    
    def get_phi_count(self) -> int:
        """Get count of detected PHI entities | 獲取檢測到的 PHI 實體數量"""
        return len(self.detected_entities)
    
    def __repr__(self) -> str:
        return (
            f"MedicalDocument(id={self.id}, "
            f"phi_count={self.get_phi_count()}, "
            f"deidentified={self.is_deidentified()})"
        )
