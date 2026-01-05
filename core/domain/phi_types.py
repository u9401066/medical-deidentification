"""
PHI Type Definitions | PHI 類型定義

Defines Protected Health Information types including standard HIPAA types
and extensible custom types discovered from regulations.
定義個人健康資訊類型，包括標準 HIPAA 類型和從法規發現的可擴展自定義類型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PHIType(str, Enum):
    """
    Protected Health Information Types | 個人健康資訊類型
    
    Standard HIPAA PHI identifiers with extensibility for custom types.
    標準 HIPAA 個資識別符,支援自定義類型擴充。
    
    This enum serves as the core type system for RAG structured output.
    此 enum 作為 RAG 結構化輸出的核心類型系統。
    
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
    
    Allows users to define custom PHI types based on specific requirements,
    especially those discovered from regulation documents via RAG.
    允許使用者根據特定需求定義自定義 PHI 類型，特別是從 RAG 法規文件中發現的類型。
    
    Examples from regulations:
    - Taiwan: 身份證字號 (National ID), 健保卡號 (Health Insurance Card)
    - Japan: マイナンバー (My Number), 保険証番号 (Insurance Number)
    - EU: National health service numbers, Tax identification numbers
    - Disease-specific: Specific rare diseases mentioned in local regulations
    
    Usage:
        >>> # From RAG regulation discovery
        >>> tw_id = CustomPHIType(
        ...     name="TW_NATIONAL_ID",
        ...     description="Taiwan National ID Number (身份證字號)",
        ...     pattern=r"[A-Z][12]\\d{8}",
        ...     examples=["A123456789", "B234567890"],
        ...     regulation_source="Taiwan PDPA Article 6",
        ...     is_high_risk=True
        ... )
        >>> 
        >>> # Use in PHIEntity
        >>> entity = PHIEntity(
        ...     type=PHIType.CUSTOM,
        ...     custom_type=tw_id,
        ...     text="A123456789",
        ...     start_pos=10,
        ...     end_pos=20,
        ...     confidence=0.95
        ... )
    """
    
    name: str  # Type name | 類型名稱 (e.g., "TW_NATIONAL_ID", "JP_MY_NUMBER")
    description: str  # Type description | 類型描述 (human-readable explanation)
    pattern: Optional[str] = None  # Regex pattern for detection | 檢測用的正則表達式
    examples: List[str] = field(default_factory=list)  # Example values | 範例值
    regulation_source: Optional[str] = None  # Source regulation | 來源法規
    is_high_risk: bool = False  # High identification risk | 高識別風險
    masking_strategy: Optional[str] = None  # Recommended masking strategy | 建議的遮罩策略
    aliases: List[str] = field(default_factory=list)  # Alternative names | 別名 (e.g., ["身份證", "ID card"])
    
    def __post_init__(self) -> None:
        """Validate custom PHI type | 驗證自定義 PHI 類型"""
        if not self.name or not self.name.strip():
            raise ValueError("Custom PHI type name cannot be empty")
        if not self.description:
            raise ValueError("Custom PHI type description is required")
    
    def __str__(self) -> str:
        """String representation for use in structured output | 用於結構化輸出的字串表示"""
        return f"CUSTOM:{self.name}"
    
    def __hash__(self) -> int:
        """Make hashable for use in sets/dicts | 使其可用於集合/字典"""
        return hash((self.name, self.description))
    
    def matches_text(self, text: str) -> bool:
        """
        Check if text matches this custom PHI type pattern | 檢查文本是否符合此自定義 PHI 類型模式
        
        Args:
            text: Text to check
            
        Returns:
            True if pattern matches or text is in examples
        """
        import re
        
        # Check examples first (exact match)
        if text in self.examples:
            return True
        
        # Check aliases (case-insensitive)
        if any(alias.lower() in text.lower() for alias in self.aliases):
            return True
        
        # Check regex pattern
        if self.pattern:
            try:
                return bool(re.match(self.pattern, text))
            except re.error:
                return False
        
        return False
