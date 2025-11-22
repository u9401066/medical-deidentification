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
    """
    Protected Health Information Types | 個人健康資訊類型
    
    Standard HIPAA PHI identifiers with extensibility for custom types.
    標準 HIPAA 個資識別符,支援自定義類型擴充。
    
    Note: Additional types can be defined based on regulation requirements.
    注意: 可根據法規要求定義額外類型。
    """
    
    # Basic Identifiers | 基本識別資訊
    NAME = "NAME"  # 姓名 (Names)
    DATE = "DATE"  # 日期 (Dates - except year)
    LOCATION = "LOCATION"  # 地點 (Geographic subdivisions smaller than state)
    
    # Numeric Identifiers | 數字識別碼
    ID = "ID"  # 一般識別碼 (General identifiers)
    MEDICAL_RECORD_NUMBER = "MEDICAL_RECORD_NUMBER"  # 病歷號 (Medical record numbers)
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"  # 帳號 (Account numbers)
    
    # Contact Information | 聯絡資訊
    CONTACT = "CONTACT"  # 一般聯絡資訊 (General contact)
    PHONE = "PHONE"  # 電話號碼 (Phone numbers)
    FAX = "FAX"  # 傳真號碼 (Fax numbers)
    EMAIL = "EMAIL"  # 電子郵件 (Email addresses)
    URL = "URL"  # 網址 (URLs)
    IP_ADDRESS = "IP_ADDRESS"  # IP 位址 (IP addresses)
    
    # Age & Demographic | 年齡與人口統計
    AGE_OVER_89 = "AGE_OVER_89"  # 年齡 >89 (Ages over 89)
    AGE_OVER_90 = "AGE_OVER_90"  # 年齡 >90 (Ages over 90 - stricter)
    
    # Biometric & Physical | 生物特徵與身體特徵
    BIOMETRIC = "BIOMETRIC"  # 生物特徵識別 (Biometric identifiers)
    PHOTO = "PHOTO"  # 照片 (Photographs)
    
    # Healthcare Facility Information | 醫療機構資訊
    HOSPITAL_NAME = "HOSPITAL_NAME"  # 醫院名稱 (Hospital names)
    DEPARTMENT_NAME = "DEPARTMENT_NAME"  # 科室名稱 (Department names)
    WARD_NUMBER = "WARD_NUMBER"  # 病房號 (Ward numbers)
    BED_NUMBER = "BED_NUMBER"  # 床號 (Bed numbers)
    
    # Medical Conditions | 醫療狀況
    RARE_DISEASE = "RARE_DISEASE"  # 罕見疾病 (Rare diseases - highly identifiable)
    GENETIC_INFO = "GENETIC_INFO"  # 基因資訊 (Genetic information)
    
    # Device & Certificate | 設備與證書
    DEVICE_ID = "DEVICE_ID"  # 設備識別碼 (Device identifiers)
    CERTIFICATE = "CERTIFICATE"  # 證書號碼 (Certificate/license numbers)
    
    # Social Identifiers | 社會識別碼
    SSN = "SSN"  # 社會安全號碼 (Social Security Number)
    INSURANCE_NUMBER = "INSURANCE_NUMBER"  # 保險號碼 (Insurance numbers)
    
    # Extensibility | 擴充性
    CUSTOM = "CUSTOM"  # 自定義類型 (Custom user-defined types)
    OTHER = "OTHER"  # 其他 (Other identifiers)
    
    @classmethod
    def get_standard_types(cls) -> List["PHIType"]:
        """
        Get standard HIPAA PHI types | 獲取標準 HIPAA PHI 類型
        
        Returns list of commonly used PHI types for baseline de-identification.
        返回基本去識別化常用的 PHI 類型列表。
        """
        return [
            cls.NAME,
            cls.DATE,
            cls.LOCATION,
            cls.MEDICAL_RECORD_NUMBER,
            cls.CONTACT,
            cls.AGE_OVER_89,
            cls.BIOMETRIC,
        ]
    
    @classmethod
    def get_strict_types(cls) -> List["PHIType"]:
        """
        Get strict PHI types for high-security scenarios | 獲取嚴格的 PHI 類型
        
        Includes additional identifiers for stricter de-identification requirements.
        包含更嚴格去識別化需求的額外識別符。
        """
        return cls.get_standard_types() + [
            cls.AGE_OVER_90,
            cls.HOSPITAL_NAME,
            cls.WARD_NUMBER,
            cls.RARE_DISEASE,
            cls.PHONE,
            cls.EMAIL,
        ]
    
    @classmethod
    def is_age_related(cls, phi_type: "PHIType") -> bool:
        """Check if PHI type is age-related | 檢查是否為年齡相關類型"""
        return phi_type in [cls.AGE_OVER_89, cls.AGE_OVER_90]
    
    @classmethod
    def is_facility_related(cls, phi_type: "PHIType") -> bool:
        """Check if PHI type is facility-related | 檢查是否為醫療機構相關類型"""
        return phi_type in [
            cls.HOSPITAL_NAME,
            cls.DEPARTMENT_NAME,
            cls.WARD_NUMBER,
            cls.BED_NUMBER,
        ]


@dataclass(frozen=True)
class CustomPHIType:
    """
    Custom PHI Type Definition | 自定義 PHI 類型定義
    
    Allows users to define custom PHI types based on specific requirements.
    允許使用者根據特定需求定義自定義 PHI 類型。
    """
    
    name: str  # Type name | 類型名稱
    description: str  # Type description | 類型描述
    pattern: Optional[str] = None  # Regex pattern for detection | 檢測用的正則表達式
    examples: List[str] = field(default_factory=list)  # Example values | 範例值
    regulation_source: Optional[str] = None  # Source regulation | 來源法規
    is_high_risk: bool = False  # High identification risk | 高識別風險
    
    def __post_init__(self) -> None:
        """Validate custom PHI type | 驗證自定義 PHI 類型"""
        if not self.name or not self.name.strip():
            raise ValueError("Custom PHI type name cannot be empty")
        if not self.description:
            raise ValueError("Custom PHI type description is required")


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
    custom_type: Optional[CustomPHIType] = None  # Custom PHI type if applicable
    
    def __post_init__(self) -> None:
        """Validate invariants | 驗證不變量"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.start_pos < 0 or self.end_pos < self.start_pos:
            raise ValueError("Invalid position range")
        if self.type == PHIType.CUSTOM and self.custom_type is None:
            raise ValueError("custom_type must be provided when type is CUSTOM")
    
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
        
        if self.custom_type and self.custom_type.is_high_risk:
            return True
        
        return False


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
    required_phi_types: List[PHIType] = field(default_factory=list)  # Required PHI types to detect
    custom_phi_types: List[CustomPHIType] = field(default_factory=list)  # Custom types from regulations
    strictness_level: str = "standard"  # "standard" or "strict"
    
    def has_rules(self) -> bool:
        """Check if any rules were retrieved | 檢查是否有檢索到規則"""
        return len(self.retrieved_rules) > 0
    
    def get_all_phi_types(self) -> List[PHIType]:
        """
        Get all PHI types to detect based on context | 根據上下文獲取所有要檢測的 PHI 類型
        
        Returns appropriate PHI types based on regulation requirements and strictness.
        根據法規要求和嚴格程度返回適當的 PHI 類型。
        """
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
