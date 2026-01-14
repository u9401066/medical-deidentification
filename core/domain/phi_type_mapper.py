"""
PHI Type Mapper | PHI 類型映射器

⚠️ DEPRECATED: This module is deprecated. Use PHITypeRegistry instead.
⚠️ 已棄用：此模組已棄用。請改用 PHITypeRegistry。

The functionality has been merged into PHITypeRegistry:
- get_phi_type_registry().map_alias(name) replaces get_default_mapper().map(name)
- registry.register_alias(alias, canonical) replaces mapper.register_custom_mapping()

This module is kept for backward compatibility but will be removed in a future version.
此模組保留供向後相容，但將在未來版本中移除。
"""

import warnings

from loguru import logger

from .phi_types import CustomPHIType, PHIType


def _deprecation_warning() -> None:
    """Issue deprecation warning"""
    warnings.warn(
        "PHITypeMapper is deprecated. Use get_phi_type_registry().map_alias() instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class PHITypeMapper:
    """
    Centralized PHI type mapping service
    集中式 PHI 類型映射服務
    
    Responsibilities:
    - Map language-specific PHI names to PHIType enum
    - Register custom PHI types dynamically
    - Handle fallback to CUSTOM type with proper naming
    - Support extensibility for new regulations
    
    Examples:
        >>> mapper = PHITypeMapper()
        >>> 
        >>> # Map Chinese name
        >>> phi_type = mapper.map("姓名")
        >>> assert phi_type == PHIType.NAME
        >>> 
        >>> # Register custom type
        >>> mapper.register_custom_mapping("醫師姓名", PHIType.NAME)
        >>> 
        >>> # Unknown type defaults to CUSTOM
        >>> phi_type, custom_name = mapper.map_with_custom("職業資訊")
        >>> assert phi_type == PHIType.CUSTOM
        >>> assert custom_name == "職業資訊"
    """

    def __init__(self):
        """Initialize with default mappings
        
        ⚠️ DEPRECATED: Use get_phi_type_registry() instead.
        """
        _deprecation_warning()
        
        # Core mappings (built-in, not modifiable at runtime)
        self._core_mappings: dict[str, PHIType] = self._build_core_mappings()

        # Extended mappings (can be added dynamically)
        self._extended_mappings: dict[str, PHIType] = {}

        # Custom type definitions (for CUSTOM types with specific meanings)
        self._custom_type_definitions: dict[str, CustomPHIType] = {}

    def _build_core_mappings(self) -> dict[str, PHIType]:
        """
        Build core Chinese-to-English PHI type mappings
        構建核心中英文 PHI 類型映射
        
        These are based on HIPAA Safe Harbor and common medical terminology.
        基於 HIPAA Safe Harbor 和常見醫療術語。
        """
        return {
            # Names / 姓名
            '姓名': PHIType.NAME,
            '名字': PHIType.NAME,
            '患者姓名': PHIType.NAME,
            '病人姓名': PHIType.NAME,
            '醫師姓名': PHIType.NAME,
            '醫生姓名': PHIType.NAME,

            # Dates / 日期
            '日期': PHIType.DATE,
            '出生日期': PHIType.DATE,
            '就診日期': PHIType.DATE,
            '住院日期': PHIType.DATE,

            # Age / 年齡
            '年齡': PHIType.AGE_OVER_89,
            '歲數': PHIType.AGE_OVER_89,
            '年齡超過89歲': PHIType.AGE_OVER_89,
            '年齡超過90歲': PHIType.AGE_OVER_90,

            # Location / 地理位置
            '地址': PHIType.LOCATION,
            '地點': PHIType.LOCATION,
            '位置': PHIType.LOCATION,
            '住址': PHIType.LOCATION,
            '小型地理區域': PHIType.LOCATION,
            '地理區域': PHIType.LOCATION,
            '地理位置': PHIType.LOCATION,

            # Contact / 聯絡方式
            '電話': PHIType.PHONE,
            '電話號碼': PHIType.PHONE,
            '聯絡電話': PHIType.PHONE,
            '手機': PHIType.PHONE,
            '傳真': PHIType.FAX,
            '傳真號碼': PHIType.FAX,
            '電子郵件': PHIType.EMAIL,
            '郵件': PHIType.EMAIL,
            'Email': PHIType.EMAIL,
            '聯絡資訊': PHIType.CONTACT,

            # IDs / 識別碼
            '身份證號碼': PHIType.ID,
            '身分證字號': PHIType.ID,
            '識別碼': PHIType.ID,
            '識別資訊': PHIType.ID,
            '病歷號': PHIType.MEDICAL_RECORD_NUMBER,
            '病歷號碼': PHIType.MEDICAL_RECORD_NUMBER,
            '醫療記錄號': PHIType.MEDICAL_RECORD_NUMBER,
            '帳號': PHIType.ACCOUNT_NUMBER,
            '帳戶號碼': PHIType.ACCOUNT_NUMBER,

            # Insurance / 保險
            '保險號碼': PHIType.INSURANCE_NUMBER,
            '醫療保險號碼': PHIType.INSURANCE_NUMBER,
            '醫療保險ID': PHIType.INSURANCE_NUMBER,
            '醫療保險 ID': PHIType.INSURANCE_NUMBER,
            '健保卡號': PHIType.INSURANCE_NUMBER,

            # Facility / 醫療機構
            '醫院': PHIType.HOSPITAL_NAME,
            '醫院名稱': PHIType.HOSPITAL_NAME,
            '醫療機構': PHIType.HOSPITAL_NAME,
            '醫療機構名稱': PHIType.HOSPITAL_NAME,
            '組織名稱': PHIType.HOSPITAL_NAME,
            '組織資訊': PHIType.HOSPITAL_NAME,
            '科室': PHIType.DEPARTMENT_NAME,
            '科室名稱': PHIType.DEPARTMENT_NAME,
            '病房號': PHIType.WARD_NUMBER,
            '床號': PHIType.BED_NUMBER,

            # Medical / 醫療資訊
            '罕見疾病': PHIType.RARE_DISEASE,
            '診斷': PHIType.RARE_DISEASE,  # Diagnoses can be rare diseases
            '基因資訊': PHIType.GENETIC_INFO,
            '遺傳資訊': PHIType.GENETIC_INFO,

            # Biometric / 生物特徵
            '照片': PHIType.PHOTO,
            '生物特徵': PHIType.BIOMETRIC,
            '指紋': PHIType.BIOMETRIC,

            # Device / 設備
            '設備識別碼': PHIType.DEVICE_ID,
            '裝置識別碼': PHIType.DEVICE_ID,

            # Certificate / 證書
            '證書': PHIType.CERTIFICATE,
            '證書號碼': PHIType.CERTIFICATE,
            '執照號碼': PHIType.CERTIFICATE,

            # Network / 網路
            '網址': PHIType.URL,
            'URL': PHIType.URL,
            'IP位址': PHIType.IP_ADDRESS,
            'IP地址': PHIType.IP_ADDRESS,

            # SSN / 社會安全號碼
            '社會安全號碼': PHIType.SSN,
            '社安號': PHIType.SSN,
        }

    def map(self, phi_type_name: str) -> PHIType | None:
        """
        Map PHI type name to PHIType enum
        映射 PHI 類型名稱到 PHIType 枚舉
        
        Args:
            phi_type_name: PHI type name (e.g., "姓名", "NAME")
            
        Returns:
            PHIType enum or None if not found
        """
        if not phi_type_name or not phi_type_name.strip():
            return None

        name = phi_type_name.strip()

        # Check extended mappings first (user-defined, higher priority)
        if name in self._extended_mappings:
            return self._extended_mappings[name]

        # Check core mappings
        if name in self._core_mappings:
            return self._core_mappings[name]

        # Try direct enum match (e.g., "NAME" -> PHIType.NAME)
        try:
            return PHIType(name.upper())
        except ValueError:
            pass

        return None

    def map_with_custom(
        self,
        phi_type_name: str
    ) -> tuple[PHIType, str | None]:
        """
        Map PHI type name, returning CUSTOM with name if not found
        映射 PHI 類型名稱，如果未找到則返回 CUSTOM 及名稱
        
        Args:
            phi_type_name: PHI type name
            
        Returns:
            Tuple of (PHIType, custom_type_name)
            - If mapped: (PHIType.NAME, None)
            - If unknown: (PHIType.CUSTOM, "原始名稱")
            - If empty: (PHIType.CUSTOM, "Unknown PHI Type")
        """
        mapped_type = self.map(phi_type_name)

        if mapped_type:
            return mapped_type, None

        # Not found, return CUSTOM with original name
        custom_name = phi_type_name.strip() if phi_type_name and phi_type_name.strip() else "Unknown PHI Type"
        logger.debug(f"Unknown PHI type '{phi_type_name}', mapping to CUSTOM: {custom_name}")

        return PHIType.CUSTOM, custom_name

    def register_custom_mapping(
        self,
        phi_type_name: str,
        target_type: PHIType
    ) -> None:
        """
        Register a custom PHI type mapping
        註冊自定義 PHI 類型映射
        
        Args:
            phi_type_name: Source name to map from
            target_type: Target PHIType to map to
            
        Examples:
            >>> mapper.register_custom_mapping("職業", PHIType.CUSTOM)
            >>> mapper.register_custom_mapping("治療資訊", PHIType.CUSTOM)
        """
        if not phi_type_name or not phi_type_name.strip():
            raise ValueError("PHI type name cannot be empty")

        self._extended_mappings[phi_type_name.strip()] = target_type
        logger.info(f"Registered custom mapping: '{phi_type_name}' -> {target_type.value}")

    def register_custom_type_definition(
        self,
        phi_type_name: str,
        custom_type: CustomPHIType
    ) -> None:
        """
        Register a full custom PHI type definition
        註冊完整的自定義 PHI 類型定義
        
        Args:
            phi_type_name: Name to map from (e.g., "身份證字號")
            custom_type: CustomPHIType definition
        """
        self._custom_type_definitions[phi_type_name] = custom_type
        # Also register mapping to CUSTOM type
        self.register_custom_mapping(phi_type_name, PHIType.CUSTOM)
        logger.info(f"Registered custom type definition: '{phi_type_name}' -> {custom_type.name}")

    def get_custom_type_definition(
        self,
        phi_type_name: str
    ) -> CustomPHIType | None:
        """
        Get custom PHI type definition if exists
        獲取自定義 PHI 類型定義（如果存在）
        
        Args:
            phi_type_name: PHI type name
            
        Returns:
            CustomPHIType or None
        """
        return self._custom_type_definitions.get(phi_type_name)

    def list_all_mappings(self) -> dict[str, str]:
        """
        List all registered mappings for debugging
        列出所有已註冊的映射供除錯使用
        
        Returns:
            Dictionary of {source_name: target_PHIType_value}
        """
        all_mappings = {}

        # Core mappings
        for name, phi_type in self._core_mappings.items():
            all_mappings[name] = phi_type.value

        # Extended mappings (may override core)
        for name, phi_type in self._extended_mappings.items():
            all_mappings[name] = phi_type.value

        return all_mappings

    def get_mapping_stats(self) -> dict[str, int]:
        """
        Get mapping statistics
        獲取映射統計資訊
        
        Returns:
            Dictionary with counts
        """
        return {
            "core_mappings": len(self._core_mappings),
            "extended_mappings": len(self._extended_mappings),
            "custom_type_definitions": len(self._custom_type_definitions),
            "total_mappings": len(self._core_mappings) + len(self._extended_mappings)
        }


# Global singleton instance
_default_mapper: PHITypeMapper | None = None


def get_default_mapper() -> PHITypeMapper:
    """
    Get default global PHI type mapper singleton
    獲取默認的全局 PHI 類型映射器單例
    
    ⚠️ DEPRECATED: Use get_phi_type_registry() instead.
    This function is deprecated and will be removed in a future version.
    
    Migration:
        # Before (deprecated):
        mapper = get_default_mapper()
        phi_type = mapper.map("姓名")
        
        # After (recommended):
        from core.domain import get_phi_type_registry
        registry = get_phi_type_registry()
        phi_type, custom_name = registry.map_alias("姓名")
    
    Returns:
        PHITypeMapper instance
    """
    _deprecation_warning()
    global _default_mapper
    if _default_mapper is None:
        _default_mapper = PHITypeMapper()
    return _default_mapper


def register_custom_mappings_from_config(config_dict: dict[str, str]) -> None:
    """
    Register custom mappings from configuration
    從配置註冊自定義映射
    
    Args:
        config_dict: Dictionary of {source_name: target_PHIType_name}
        
    Examples:
        >>> register_custom_mappings_from_config({
        ...     "職業": "CUSTOM",
        ...     "治療": "CUSTOM",
        ...     "醫師資訊": "NAME"
        ... })
    """
    mapper = get_default_mapper()

    for source_name, target_name in config_dict.items():
        try:
            target_type = PHIType(target_name.upper())
            mapper.register_custom_mapping(source_name, target_type)
        except ValueError:
            logger.warning(f"Invalid target PHI type: {target_name}, skipping mapping for {source_name}")
