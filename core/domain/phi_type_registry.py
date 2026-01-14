"""
PHI Type Registry | PHI 類型註冊中心

Central registry for managing all PHI types (static + dynamic).
中央註冊中心，管理所有 PHI 類型（靜態 + 動態）。

Features:
- Base types from PHIType enum (HIPAA standard)
- Custom types registered at runtime
- Types discovered from RAG regulation documents
- Dynamic prompt generation for LLM

特點：
- 來自 PHIType enum 的基礎類型（HIPAA 標準）
- 運行時註冊的自訂類型
- 從 RAG 法規文件發現的類型
- 為 LLM 動態生成 prompt

Usage:
    >>> registry = get_phi_type_registry()
    >>>
    >>> # Register custom type
    >>> registry.register_custom_type(CustomPHIType(
    ...     name="TW_NATIONAL_ID",
    ...     description="Taiwan National ID (身份證字號)",
    ...     pattern=r"[A-Z][12]\\d{8}",
    ... ))
    >>>
    >>> # Get all types for prompt
    >>> prompt_text = registry.get_types_for_prompt()
    >>>
    >>> # Record discovered type from LLM output
    >>> registry.record_discovered_type("職業資訊", "Occupation information")
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

from .phi_types import CustomPHIType, PHIType

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class RegisteredType:
    """
    Registered PHI type information
    已註冊的 PHI 類型資訊
    """
    name: str
    description: str
    source: str  # "base" | "custom" | "discovered" | "rag"
    base_type: PHIType | None = None  # For base types
    custom_type: CustomPHIType | None = None  # For custom types
    examples: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

    @property
    def is_base_type(self) -> bool:
        return self.source == "base"

    @property
    def display_name(self) -> str:
        """Name used in LLM prompt"""
        if self.is_base_type:
            return self.name
        return f"CUSTOM:{self.name}"


class PHITypeRegistry:
    """
    Central PHI Type Registry (Singleton)
    中央 PHI 類型註冊中心（單例）

    Manages all PHI types for the de-identification system:
    - Base types: Standard HIPAA PHI types (PHIType enum)
    - Custom types: User-defined types (CustomPHIType)
    - Discovered types: Types found by LLM during processing
    - RAG types: Types extracted from regulation documents

    管理去識別化系統的所有 PHI 類型：
    - 基礎類型：標準 HIPAA PHI 類型（PHIType enum）
    - 自訂類型：使用者定義的類型（CustomPHIType）
    - 發現類型：LLM 處理過程中發現的類型
    - RAG 類型：從法規文件提取的類型
    """

    _instance: PHITypeRegistry | None = None
    _lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> PHITypeRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._types: dict[str, RegisteredType] = {}
        self._aliases: dict[str, str] = {}  # alias -> canonical name
        self._discovery_callbacks: list[Callable[[str, str], None]] = []
        self._initialize_base_types()
        self._initialize_aliases()
        self._initialized = True

        logger.info(f"PHITypeRegistry initialized with {len(self._types)} base types, {len(self._aliases)} aliases")

    def _initialize_base_types(self) -> None:
        """Initialize with base PHIType enum values"""
        # Base type descriptions (bilingual)
        descriptions = {
            PHIType.NAME: "Names (姓名)",
            PHIType.DATE: "Dates except year (日期，年份除外)",
            PHIType.LOCATION: "Geographic locations smaller than state (小於州/省的地理位置)",
            PHIType.ID: "General identifiers (一般識別碼)",
            PHIType.MEDICAL_RECORD_NUMBER: "Medical record numbers (病歷號)",
            PHIType.ACCOUNT_NUMBER: "Account numbers (帳號)",
            PHIType.CONTACT: "General contact information (一般聯絡資訊)",
            PHIType.PHONE: "Phone numbers (電話號碼)",
            PHIType.FAX: "Fax numbers (傳真號碼)",
            PHIType.EMAIL: "Email addresses (電子郵件)",
            PHIType.URL: "Web URLs (網址)",
            PHIType.IP_ADDRESS: "IP addresses (IP 位址)",
            PHIType.AGE_OVER_89: "Ages over 89 (年齡超過 89 歲)",
            PHIType.AGE_OVER_90: "Ages over 90 (年齡超過 90 歲)",
            PHIType.BIOMETRIC: "Biometric identifiers (生物特徵識別)",
            PHIType.PHOTO: "Photographs (照片)",
            PHIType.HOSPITAL_NAME: "Hospital/facility names (醫院/機構名稱)",
            PHIType.DEPARTMENT_NAME: "Department names (科室名稱)",
            PHIType.WARD_NUMBER: "Ward numbers (病房號)",
            PHIType.BED_NUMBER: "Bed numbers (床號)",
            PHIType.RARE_DISEASE: "Rare diseases (罕見疾病)",
            PHIType.GENETIC_INFO: "Genetic information (基因資訊)",
            PHIType.DEVICE_ID: "Device identifiers (設備識別碼)",
            PHIType.CERTIFICATE: "Certificate/license numbers (證書/執照號碼)",
            PHIType.SSN: "Social Security Numbers (社會安全號碼)",
            PHIType.INSURANCE_NUMBER: "Insurance numbers (保險號碼)",
            PHIType.CUSTOM: "Custom user-defined types (自訂類型)",
            PHIType.OTHER: "Other identifiers (其他識別資訊)",
        }

        for phi_type in PHIType:
            self._types[phi_type.value] = RegisteredType(
                name=phi_type.value,
                description=descriptions.get(phi_type, phi_type.value),
                source="base",
                base_type=phi_type,
            )

    def _initialize_aliases(self) -> None:
        """
        Initialize Chinese and English aliases for PHI types.
        初始化 PHI 類型的中英文別名。

        These mappings allow flexible input from LLM outputs.
        這些映射允許從 LLM 輸出中靈活輸入。
        """
        # Aliases map to canonical PHIType enum names
        alias_mappings: dict[str, list[str]] = {
            # Names / 姓名
            "NAME": ["姓名", "名字", "患者姓名", "病人姓名", "醫師姓名", "醫生姓名", "name", "patient_name"],
            # Dates / 日期
            "DATE": ["日期", "出生日期", "就診日期", "住院日期", "date", "birth_date"],
            # Age / 年齡
            "AGE_OVER_89": ["年齡", "歲數", "年齡超過89歲", "age", "age_over_89"],
            "AGE_OVER_90": ["年齡超過90歲", "age_over_90"],
            # Location / 地理位置
            "LOCATION": ["地址", "地點", "位置", "住址", "小型地理區域", "地理區域", "地理位置", "address", "location"],
            # Contact / 聯絡方式
            "PHONE": ["電話", "電話號碼", "聯絡電話", "手機", "phone", "mobile"],
            "FAX": ["傳真", "傳真號碼", "fax"],
            "EMAIL": ["電子郵件", "郵件", "email", "e-mail"],
            "CONTACT": ["聯絡資訊", "contact", "contact_info"],
            # IDs / 識別碼
            "ID": ["身份證號碼", "身分證字號", "識別碼", "識別資訊", "id", "identifier"],
            "MEDICAL_RECORD_NUMBER": ["病歷號", "病歷號碼", "醫療記錄號", "mrn", "medical_record"],
            "ACCOUNT_NUMBER": ["帳號", "帳戶號碼", "account", "account_number"],
            # Insurance / 保險
            "INSURANCE_NUMBER": ["保險號碼", "醫療保險號碼", "醫療保險ID", "健保卡號", "insurance", "insurance_id"],
            # Facility / 醫療機構
            "HOSPITAL_NAME": ["醫院", "醫院名稱", "醫療機構", "醫療機構名稱", "組織名稱", "組織資訊", "hospital", "facility"],
            "DEPARTMENT_NAME": ["科室", "科室名稱", "department"],
            "WARD_NUMBER": ["病房號", "ward", "ward_number"],
            "BED_NUMBER": ["床號", "bed", "bed_number"],
            # Medical / 醫療資訊
            "RARE_DISEASE": ["罕見疾病", "診斷", "rare_disease"],
            "GENETIC_INFO": ["基因資訊", "遺傳資訊", "genetic", "genetic_info"],
            # Biometric / 生物特徵
            "PHOTO": ["照片", "photo", "photograph"],
            "BIOMETRIC": ["生物特徵", "指紋", "biometric", "fingerprint"],
            # Device / 設備
            "DEVICE_ID": ["設備識別碼", "裝置識別碼", "device", "device_id"],
            # Certificate / 證書
            "CERTIFICATE": ["證書", "證書號碼", "執照號碼", "certificate", "license"],
            # Network / 網路
            "URL": ["網址", "url", "website"],
            "IP_ADDRESS": ["IP位址", "IP地址", "ip", "ip_address"],
            # SSN / 社會安全號碼
            "SSN": ["社會安全號碼", "社安號", "ssn", "social_security"],
        }

        for canonical_name, aliases in alias_mappings.items():
            for alias in aliases:
                # Store lowercase for case-insensitive matching
                self._aliases[alias.lower()] = canonical_name

    # =========================================================================
    # Alias Mapping Methods (from PHITypeMapper)
    # =========================================================================

    def map_alias(self, name: str) -> tuple[PHIType, str | None]:
        """
        Map a PHI type name/alias to PHIType enum.
        將 PHI 類型名稱/別名映射到 PHIType enum。

        This is the main entry point for converting LLM output to PHIType.
        這是將 LLM 輸出轉換為 PHIType 的主要入口點。

        Args:
            name: PHI type name (e.g., "姓名", "NAME", "name")

        Returns:
            Tuple of (PHIType, custom_type_name)
            - If mapped: (PHIType.NAME, None)
            - If unknown: (PHIType.CUSTOM, "original_name")
        """
        if not name or not name.strip():
            return PHIType.CUSTOM, "Unknown PHI Type"

        name_clean = name.strip()
        name_lower = name_clean.lower()
        name_upper = name_clean.upper().replace(" ", "_").replace("-", "_")

        # 1. Try direct PHIType enum match
        try:
            return PHIType[name_upper], None
        except KeyError:
            pass

        # 2. Try alias lookup (case-insensitive)
        if name_lower in self._aliases:
            canonical = self._aliases[name_lower]
            try:
                return PHIType[canonical], None
            except KeyError:
                pass

        # 3. Check if it's a registered custom/discovered type
        if name_clean in self._types:
            reg_type = self._types[name_clean]
            if reg_type.base_type:
                return reg_type.base_type, None
            return PHIType.CUSTOM, name_clean

        # 4. Unknown type - return CUSTOM
        logger.debug(f"Unknown PHI type '{name}', mapping to CUSTOM")
        return PHIType.CUSTOM, name_clean

    def register_alias(self, alias: str, canonical_name: str) -> None:
        """
        Register a new alias for a PHI type.
        註冊 PHI 類型的新別名。

        Args:
            alias: The alias to register
            canonical_name: The canonical PHIType name (e.g., "NAME")
        """
        self._aliases[alias.lower()] = canonical_name.upper()
        logger.debug(f"Registered alias: '{alias}' -> {canonical_name}")

    def get_all_aliases(self) -> dict[str, str]:
        """Get all registered aliases"""
        return dict(self._aliases)

    # =========================================================================
    # Registration Methods
    # =========================================================================

    def register_custom_type(
        self,
        custom_type: CustomPHIType,
        overwrite: bool = False
    ) -> None:
        """
        Register a custom PHI type
        註冊自訂 PHI 類型

        Args:
            custom_type: CustomPHIType instance
            overwrite: Whether to overwrite existing type
        """
        name = custom_type.name

        if name in self._types and not overwrite:
            logger.warning(f"PHI type '{name}' already registered, skipping")
            return

        self._types[name] = RegisteredType(
            name=name,
            description=custom_type.description,
            source="custom",
            custom_type=custom_type,
            examples=custom_type.examples,
            aliases=custom_type.aliases,
        )

        logger.info(f"Registered custom PHI type: {name}")

    def register_rag_type(
        self,
        name: str,
        description: str,
        regulation_source: str | None = None,
        examples: list[str] | None = None,
    ) -> None:
        """
        Register a PHI type discovered from RAG regulation documents
        註冊從 RAG 法規文件發現的 PHI 類型

        Args:
            name: Type name
            description: Type description
            regulation_source: Source regulation document
            examples: Example values
        """
        if name in self._types:
            logger.debug(f"PHI type '{name}' already registered")
            return

        custom_type = CustomPHIType(
            name=name,
            description=description,
            regulation_source=regulation_source,
            examples=examples or [],
        )

        self._types[name] = RegisteredType(
            name=name,
            description=description,
            source="rag",
            custom_type=custom_type,
            examples=examples or [],
        )

        logger.info(f"Registered RAG-discovered PHI type: {name} (from: {regulation_source})")

    def record_discovered_type(
        self,
        name: str,
        description: str | None = None,
    ) -> None:
        """
        Record a PHI type discovered by LLM during processing
        記錄 LLM 處理過程中發現的 PHI 類型

        These are types the LLM identified that weren't in the registry.
        這些是 LLM 識別出但不在註冊表中的類型。

        Args:
            name: Type name from LLM output
            description: Optional description
        """
        if name in self._types:
            return

        self._types[name] = RegisteredType(
            name=name,
            description=description or f"Discovered type: {name}",
            source="discovered",
        )

        logger.info(f"Recorded discovered PHI type: {name}")

        # Notify callbacks
        for callback in self._discovery_callbacks:
            try:
                callback(name, description or "")
            except Exception as e:
                logger.error(f"Discovery callback error: {e}")

    def on_type_discovered(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for when new types are discovered"""
        self._discovery_callbacks.append(callback)

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_type(self, name: str) -> RegisteredType | None:
        """Get registered type by name"""
        return self._types.get(name)

    def get_base_type(self, name: str) -> PHIType | None:
        """
        Get PHIType enum for a type name
        取得類型名稱對應的 PHIType enum

        Returns PHIType.CUSTOM for custom/discovered types.
        """
        reg_type = self._types.get(name)
        if reg_type and reg_type.base_type:
            return reg_type.base_type
        return PHIType.CUSTOM if name in self._types else None

    def is_known_type(self, name: str) -> bool:
        """Check if type is registered"""
        return name in self._types

    def get_all_type_names(self) -> list[str]:
        """Get all registered type names"""
        return list(self._types.keys())

    def get_base_type_names(self) -> list[str]:
        """Get only base (HIPAA) type names"""
        return [name for name, t in self._types.items() if t.source == "base"]

    def get_custom_type_names(self) -> list[str]:
        """Get custom + RAG + discovered type names"""
        return [name for name, t in self._types.items() if t.source != "base"]

    # =========================================================================
    # Prompt Generation
    # =========================================================================

    def get_types_for_prompt(
        self,
        include_base: bool = True,
        include_custom: bool = True,
        include_descriptions: bool = True,
        format: str = "list",  # "list" | "json" | "markdown"
    ) -> str:
        """
        Generate PHI types text for LLM prompt
        生成用於 LLM prompt 的 PHI 類型文本

        Args:
            include_base: Include base HIPAA types
            include_custom: Include custom/RAG/discovered types
            include_descriptions: Include type descriptions
            format: Output format

        Returns:
            Formatted string of available PHI types
        """
        types_to_include = []

        for name, reg_type in self._types.items():
            # Skip CUSTOM and OTHER base types (they're meta-types)
            if reg_type.is_base_type and name in ("CUSTOM", "OTHER"):
                continue

            if reg_type.source == "base" and not include_base:
                continue
            if reg_type.source != "base" and not include_custom:
                continue

            types_to_include.append(reg_type)

        if format == "list":
            return self._format_as_list(types_to_include, include_descriptions)
        elif format == "json":
            return self._format_as_json(types_to_include, include_descriptions)
        elif format == "markdown":
            return self._format_as_markdown(types_to_include, include_descriptions)
        else:
            return self._format_as_list(types_to_include, include_descriptions)

    def _format_as_list(
        self,
        types: list[RegisteredType],
        include_descriptions: bool
    ) -> str:
        """Format as simple list"""
        lines = []

        # Group by source
        base_types = [t for t in types if t.source == "base"]
        custom_types = [t for t in types if t.source != "base"]

        if base_types:
            lines.append("Standard PHI Types (標準 PHI 類型):")
            for t in base_types:
                if include_descriptions:
                    lines.append(f"  - {t.name}: {t.description}")
                else:
                    lines.append(f"  - {t.name}")

        if custom_types:
            lines.append("")
            lines.append("Custom PHI Types (自訂 PHI 類型):")
            for t in custom_types:
                display = f"CUSTOM:{t.name}"
                if include_descriptions:
                    lines.append(f"  - {display}: {t.description}")
                else:
                    lines.append(f"  - {display}")

        lines.append("")
        lines.append("For new/unknown types, use: CUSTOM:<type_name>")
        lines.append("對於新的/未知類型，使用：CUSTOM:<類型名稱>")

        return "\n".join(lines)

    def _format_as_json(
        self,
        types: list[RegisteredType],
        include_descriptions: bool
    ) -> str:
        """Format as JSON-like structure"""
        import json

        type_dict: dict[str, str] = {}
        for t in types:
            key = t.name if t.source == "base" else f"CUSTOM:{t.name}"
            if include_descriptions:
                type_dict[key] = t.description
            else:
                type_dict[key] = ""

        return json.dumps(type_dict, ensure_ascii=False, indent=2)

    def _format_as_markdown(
        self,
        types: list[RegisteredType],
        include_descriptions: bool
    ) -> str:
        """Format as markdown table"""
        lines = ["| Type | Description |", "|------|-------------|"]

        for t in types:
            display = t.name if t.source == "base" else f"CUSTOM:{t.name}"
            desc = t.description if include_descriptions else ""
            lines.append(f"| {display} | {desc} |")

        return "\n".join(lines)

    def get_type_enum_values(self) -> list[str]:
        """
        Get list of valid type values for structured output schema
        取得結構化輸出 schema 的有效類型值列表

        This is used to generate the JSON schema for LLM structured output.
        """
        values = []

        # Add base types
        for name, t in self._types.items():
            if t.source == "base":
                values.append(name)

        # Add custom types with CUSTOM: prefix
        for name, t in self._types.items():
            if t.source != "base":
                values.append(f"CUSTOM:{name}")

        return values

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def clear_discovered_types(self) -> None:
        """Clear all discovered types (keep base and custom)"""
        to_remove = [name for name, t in self._types.items() if t.source == "discovered"]
        for name in to_remove:
            del self._types[name]
        logger.info(f"Cleared {len(to_remove)} discovered types")

    def export_custom_types(self) -> list[dict]:
        """Export custom types as list of dicts (for persistence)"""
        result = []
        for reg_type in self._types.values():
            if reg_type.source in ("custom", "rag"):
                result.append({
                    "name": reg_type.name,
                    "description": reg_type.description,
                    "source": reg_type.source,
                    "examples": reg_type.examples,
                    "aliases": reg_type.aliases,
                })
        return result

    def import_custom_types(self, types_data: list[dict]) -> int:
        """Import custom types from list of dicts"""
        count = 0
        for data in types_data:
            name = data.get("name")
            if not name or name in self._types:
                continue

            self._types[name] = RegisteredType(
                name=name,
                description=data.get("description", name),
                source=data.get("source", "custom"),
                examples=data.get("examples", []),
                aliases=data.get("aliases", []),
            )
            count += 1

        logger.info(f"Imported {count} custom types")
        return count

    def __len__(self) -> int:
        return len(self._types)

    def __contains__(self, name: str) -> bool:
        return name in self._types


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_registry: PHITypeRegistry | None = None


def get_phi_type_registry() -> PHITypeRegistry:
    """
    Get the global PHI type registry singleton
    取得全域 PHI 類型註冊中心單例
    """
    global _registry
    if _registry is None:
        _registry = PHITypeRegistry()
    return _registry


def reset_phi_type_registry() -> None:
    """Reset the registry (mainly for testing)"""
    global _registry
    PHITypeRegistry._instance = None
    _registry = None
