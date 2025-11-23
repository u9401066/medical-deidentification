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
- Field validators for data integrity
- Type mapping integration with PHITypeMapper

設計原則：
- LLM 結構化輸出的 DTO（Pydantic 驗證）
- 轉換方法到領域實體（to_phi_entity()）
- 欄位驗證器確保數據完整性
- 與 PHITypeMapper 的類型映射整合
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger

from .phi_types import PHIType, CustomPHIType
from .entities import PHIEntity
from .phi_type_mapper import get_default_mapper


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
    phi_type: PHIType = Field(
        description="PHI type enum (e.g., PHIType.NAME, PHIType.AGE_OVER_89)"
    )
    custom_type_name: Optional[str] = Field(
        default=None,
        description="Custom PHI type name if phi_type is CUSTOM"
    )
    custom_type_description: Optional[str] = Field(
        default=None,
        description="Description of custom PHI type"
    )
    start_position: int = Field(
        ge=0,
        description="Character position where entity starts (0-indexed)"
    )
    end_position: int = Field(
        ge=0,
        description="Character position where entity ends (exclusive)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level (0.0-1.0)"
    )
    reason: str = Field(
        description="Explanation of why this is PHI according to regulations"
    )
    regulation_source: Optional[str] = Field(
        default=None,
        description="Source regulation"
    )
    masking_action: Optional[str] = Field(
        default=None,
        description="Recommended masking action"
    )
    is_custom_from_regulation: bool = Field(
        default=False,
        description="Whether this PHI type was discovered from regulations"
    )
    
    @field_validator('end_position')
    @classmethod
    def validate_position_range(cls, v: int, info) -> int:
        """
        Ensure end_position >= start_position
        確保結束位置 >= 起始位置
        """
        if 'start_position' in info.data and v < info.data['start_position']:
            raise ValueError('end_position must be >= start_position')
        return v
    
    @field_validator('custom_type_name')
    @classmethod
    def validate_custom_type(cls, v: Optional[str], info) -> Optional[str]:
        """
        Ensure CUSTOM type has custom_type_name
        確保 CUSTOM 類型有 custom_type_name
        """
        if 'phi_type' in info.data and info.data['phi_type'] == PHIType.CUSTOM:
            if not v or not v.strip():
                # Provide default fallback instead of raising error
                fallback_name = "Unknown PHI Type"
                if 'entity_text' in info.data and info.data['entity_text']:
                    fallback_name = f"Custom PHI: {info.data['entity_text'][:50]}"
                logger.warning(f"CUSTOM type missing custom_type_name, using fallback: {fallback_name}")
                return fallback_name
        return v
    
    @field_validator('phi_type', mode='before')
    @classmethod
    def normalize_phi_type(cls, v, info) -> PHIType:
        """
        Convert string to PHIType enum using domain PHITypeMapper
        使用領域層的 PHITypeMapper 將字串轉換為 PHIType 枚舉
        
        This integrates with the centralized type mapping system in domain layer.
        這與領域層中的集中式類型映射系統整合。
        """
        if isinstance(v, PHIType):
            return v
        
        if isinstance(v, str):
            # Use domain-layer PHITypeMapper for all mappings
            mapper = get_default_mapper()
            mapped_type, custom_name = mapper.map_with_custom(v)
            
            # CRITICAL FIX: If mapped to CUSTOM, ALWAYS store the custom_type_name
            # This prevents "custom_type must be provided" error in PHIEntity
            if mapped_type == PHIType.CUSTOM:
                if custom_name:
                    # Store original custom name from mapper
                    if hasattr(info, 'data'):
                        info.data['custom_type_name'] = custom_name
                else:
                    # Fallback: use original string as custom type name
                    logger.warning(f"PHI type '{v}' mapped to CUSTOM but no custom_name provided, using original string")
                    if hasattr(info, 'data'):
                        info.data['custom_type_name'] = v
            
            return mapped_type
        
        raise ValueError(f"Invalid phi_type: {v}")
    
    def to_phi_entity(self) -> PHIEntity:
        """
        Convert to PHIEntity domain model
        轉換為 PHIEntity 領域模型
        
        This bridges the DTO layer (infrastructure) to the domain layer.
        這連接了 DTO 層（基礎設施）和領域層。
        
        Returns:
            PHIEntity: Immutable domain entity
        """
        custom_type = None
        if self.phi_type == PHIType.CUSTOM and self.custom_type_name:
            # CustomPHIType is a dataclass with all fields
            from dataclasses import replace
            custom_type = CustomPHIType(
                name=self.custom_type_name,
                description=self.custom_type_description or self.reason,
                pattern=None,
                examples=[],
                regulation_source=self.regulation_source,
                is_high_risk=False,
                masking_strategy=self.masking_action,
                aliases=[],
            )
        
        return PHIEntity(
            type=self.phi_type,
            text=self.entity_text,
            start_pos=self.start_position,
            end_pos=self.end_position,
            confidence=self.confidence,
            reason=self.reason,
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
    
    entities: List[PHIIdentificationResult] = Field(
        default_factory=list,
        description="List of detected PHI entities"
    )
    total_entities: Optional[int] = Field(
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
