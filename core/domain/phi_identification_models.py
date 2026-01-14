"""
PHI Identification Models | PHI 識別模型

Pydantic models for PHI identification structured output.
用於 PHI 識別結構化輸出的 Pydantic 模型。

These models serve as data transfer objects (DTOs) between the LLM layer
and the domain layer, providing validation and type safety.
這些模型作為 LLM 層和領域層之間的數據傳輸對象（DTO），提供驗證和類型安全。

Design Principles:
- DTOs for LLM structured output (Pydantic validation)
- Conversion methods to domain entities (to_phi_entity())
- Support for dynamic PHI types (base + custom + discovered)
- model_validator for cross-field normalization

設計原則：
- LLM 結構化輸出的 DTO（Pydantic 驗證）
- 轉換方法到領域實體（to_phi_entity()）
- 支援動態 PHI 類型（基礎 + 自訂 + 發現）
- 使用 model_validator 進行跨欄位正規化
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from .entities import PHIEntity
from .phi_type_registry import get_phi_type_registry
from .phi_types import CustomPHIType, PHIType


class PHIIdentificationResult(BaseModel):
    """
    單個 PHI 實體的結構化識別結果

    Structured Output Model for LLM PHI identification results.
    This is a DTO (Data Transfer Object) that validates LLM output
    before converting to domain entities.

    這是一個 DTO（數據傳輸對象），在轉換為領域實體之前驗證 LLM 輸出。

    Fields:
        entity_text: The exact PHI text from document
        phi_type: PHI type (uses domain PHIType enum)
        custom_type_name: Custom type name for CUSTOM types
        start_position: Start character position (0-indexed)
        end_position: End character position (exclusive)
        confidence: Confidence score (0.0-1.0)
        reason: Explanation why this is PHI
        regulation_source: Source regulation reference
        masking_action: Recommended masking strategy
        is_custom_from_regulation: Whether discovered from regulations
    """

    entity_text: str = Field(
        description="The exact text from the document that was identified as PHI"
    )
    phi_type: PHIType | None = Field(
        default=PHIType.NAME,
        description="PHI type enum (e.g., PHIType.NAME, PHIType.AGE_OVER_89)"
    )
    custom_type_name: str | None = Field(
        default=None,
        description="Custom PHI type name if phi_type is CUSTOM"
    )
    custom_type_description: str | None = Field(
        default=None,
        description="Description of custom PHI type"
    )
    start_position: int | None = Field(
        default=0,
        ge=0,
        description="Character position where entity starts (0-indexed)"
    )
    end_position: int | None = Field(
        default=0,
        ge=0,
        description="Character position where entity ends (exclusive)"
    )
    confidence: float | None = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level (0.0-1.0)"
    )
    reason: str | None = Field(
        default="Identified as PHI",
        description="Explanation of why this is PHI according to regulations"
    )
    regulation_source: str | None = Field(
        default=None,
        description="Source regulation"
    )
    masking_action: str | None = Field(
        default=None,
        description="Recommended masking action"
    )
    is_custom_from_regulation: bool = Field(
        default=False,
        description="Whether this PHI type was discovered from regulations"
    )

    @field_validator('end_position')
    @classmethod
    def validate_position_range(cls, v: int | None, info: ValidationInfo) -> int | None:
        """
        Ensure end_position >= start_position
        確保結束位置 >= 起始位置
        """
        if v is None:
            return 0
        start = info.data.get('start_position') if info.data else None
        if start is not None and v < start:
            return int(start)  # Auto-fix instead of raising error
        return v

    @model_validator(mode='before')
    @classmethod
    def normalize_phi_type_and_custom(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize phi_type and handle dynamic/custom types.
        正規化 phi_type 並處理動態/自訂類型。

        This uses model_validator(mode='before') to properly set both
        phi_type and custom_type_name in a single pass.
        使用 model_validator(mode='before') 在單次處理中正確設定 phi_type 和 custom_type_name。

        Supported formats from LLM:
        - Standard enum: "NAME", "DATE", "SSN", etc.
        - Custom prefix: "CUSTOM:xxx" → phi_type=CUSTOM, custom_type_name=xxx
        - Unknown string: Registered as discovered type

        支援的 LLM 輸出格式：
        - 標準枚舉：「NAME」、「DATE」、「SSN」等
        - 自訂前綴：「CUSTOM:xxx」→ phi_type=CUSTOM, custom_type_name=xxx
        - 未知字串：註冊為發現的類型
        """
        if not isinstance(data, dict):
            return data

        phi_type_raw = data.get('phi_type')

        # Already a PHIType enum, no processing needed
        if isinstance(phi_type_raw, PHIType):
            return data

        if not isinstance(phi_type_raw, str):
            return data

        phi_type_str = phi_type_raw.strip()
        registry = get_phi_type_registry()

        # Case 1: "CUSTOM:xxx" format from LLM
        if phi_type_str.upper().startswith('CUSTOM:'):
            custom_name = phi_type_str[7:].strip()
            data['phi_type'] = PHIType.CUSTOM
            data['custom_type_name'] = custom_name or 'Unknown Custom Type'

            # Record as discovered type
            registry.record_discovered_type(
                custom_name,
                description=data.get('reason'),
            )
            logger.debug(f"Recorded discovered type from LLM: {custom_name}")
            return data

        # Case 2: Use registry's unified mapping (handles enum + aliases + custom)
        mapped_type, custom_name = registry.map_alias(phi_type_str)
        data['phi_type'] = mapped_type

        if mapped_type == PHIType.CUSTOM:
            data['custom_type_name'] = custom_name
            # Record as discovered type if not already known
            if not registry.is_known_type(custom_name or phi_type_str):
                registry.record_discovered_type(
                    custom_name or phi_type_str,
                    description=data.get('reason'),
                )

        return data

    @field_validator('custom_type_name')
    @classmethod
    def validate_custom_type(cls, v: str | None, info: ValidationInfo) -> str | None:
        """
        Ensure CUSTOM type has custom_type_name
        確保 CUSTOM 類型有 custom_type_name
        """
        data = info.data or {}
        if data.get('phi_type') == PHIType.CUSTOM:
            if not v or not v.strip():
                # Provide default fallback instead of raising error
                fallback_name = "Unknown PHI Type"
                entity_text = data.get('entity_text')
                if entity_text:
                    fallback_name = f"Custom PHI: {str(entity_text)[:50]}"
                logger.warning(f"CUSTOM type missing custom_type_name, using fallback: {fallback_name}")
                return fallback_name
        return v

    def to_phi_entity(self) -> PHIEntity:
        """
        Convert to PHIEntity domain model
        轉換為 PHIEntity 領域模型

        This bridges the DTO layer (infrastructure) to the domain layer.
        這連接了 DTO 層（基礎設施）和領域層。

        Returns:
            PHIEntity: Immutable domain entity
        """
        # Handle optional fields with defaults
        phi_type = self.phi_type or PHIType.NAME
        start_pos = self.start_position or 0
        end_pos = self.end_position or 0
        confidence = self.confidence if self.confidence is not None else 1.0
        reason = self.reason or "Identified as PHI"

        custom_type = None
        if phi_type == PHIType.CUSTOM and self.custom_type_name:
            # CustomPHIType is a dataclass with all fields
            custom_type = CustomPHIType(
                name=self.custom_type_name,
                description=self.custom_type_description or reason,
                pattern=None,
                examples=[],
                regulation_source=self.regulation_source,
                is_high_risk=False,
                masking_strategy=self.masking_action,
                aliases=[],
            )

        return PHIEntity(
            type=phi_type,
            text=self.entity_text,
            start_pos=start_pos,
            end_pos=end_pos,
            confidence=confidence,
            reason=reason,
            regulation_source=self.regulation_source,
            custom_type=custom_type,
        )


class PHIDetectionResponse(BaseModel):
    """
    Complete PHI detection response (multiple entities)
    完整的 PHI 檢測響應（多個實體）

    This model represents the complete structured output from LLM
    for PHI identification in a document.

    這個模型代表 LLM 對文檔中 PHI 識別的完整結構化輸出。

    Fields:
        entities: List of identified PHI entities
        total_entities: Total count (validated against list length)
        has_phi: Whether any PHI was detected
    """

    entities: list[PHIIdentificationResult] = Field(
        default_factory=list,
        description="List of detected PHI entities"
    )
    total_entities: int | None = Field(
        default=None,
        ge=0,
        description="Total number of entities detected (optional, will be auto-calculated)"
    )
    has_phi: bool = Field(
        description="Whether any PHI was detected"
    )

    @model_validator(mode='after')
    def validate_and_fix_total(self) -> 'PHIDetectionResponse':
        """
        Auto-calculate total_entities and remove duplicates
        自動計算 total_entities 並移除重複
        """
        # Remove duplicate entities (same text at same position)
        seen = set()
        unique_entities = []
        for entity in self.entities:
            key = (entity.entity_text, entity.start_position, entity.end_position)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        self.entities = unique_entities
        # Auto-calculate total_entities from actual list length
        self.total_entities = len(self.entities)
        # Update has_phi based on actual entities
        self.has_phi = len(self.entities) > 0

        return self


class PHIIdentificationConfig(BaseModel):
    """
    Configuration for PHI identification
    PHI 識別配置

    This configuration model controls the behavior of PHI identification process.
    這個配置模型控制 PHI 識別過程的行為。

    Fields:
        llm_config: LLM provider and model settings (dict format to avoid circular import)
        use_structured_output: Use Pydantic structured output
        retrieve_regulation_context: Retrieve regulations from vector store
        regulation_context_k: Number of regulation docs to retrieve
    """

    # Use Any to avoid circular dependency with infrastructure layer
    # The actual LLMConfig will be validated at runtime
    llm_config: Any = Field(
        default_factory=dict,
        description="LLM configuration (dict or LLMConfig object)"
    )
    use_structured_output: bool = Field(
        default=True,
        description="Use LLM structured output (recommended)"
    )
    retrieve_regulation_context: bool = Field(
        default=True,
        description="Retrieve regulation context before identification"
    )
    regulation_context_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of regulation documents to retrieve for context"
    )
