"""
Domain Layer | 領域層

Contains core business logic and domain models following DDD principles.
包含遵循 DDD 原則的核心業務邏輯與領域模型。

DDD Structure (領域驅動設計結構):

├── phi_types.py               - Type definitions (PHIType enum, CustomPHIType)
│                                類型定義（PHI 類型枚舉、自定義類型）
│
├── entities.py                - Domain entities (PHIEntity)
│                                領域實體（PHI 實體）
│
├── value_objects.py           - Value objects (SupportedLanguage, RegulationContext, etc.)
│                                值物件（支援語言、法規上下文等）
│
├── aggregates.py              - Aggregate roots (MedicalDocument)
│                                聚合根（醫療文件）
│
├── phi_type_mapper.py         - PHI type mapping service
│                                PHI 類型映射服務
│
└── phi_identification_models.py - DTOs for LLM structured output
                                   LLM 結構化輸出的 DTO

This module provides a unified export interface for all domain models.
此模組提供所有領域模型的統一導出接口。
"""

# Type Definitions | 類型定義
# Aggregates | 聚合
from .aggregates import MedicalDocument

# Configuration Models | 配置模型
from .configs import (
    EmbeddingsConfig,
    MedicalRetrieverConfig,
    RegulationRetrievalConfig,
    RegulationRetrieverConfig,
    RegulationStoreConfig,
)

# Entities | 實體
from .entities import PHIEntity

# Document Loader Models | 文檔載入模型
from .loader_models import (
    DocumentFormat,
    LoadedDocument,
    LoaderConfig,
)
from .loader_models import (
    DocumentMetadata as LoaderDocumentMetadata,
)
from .masking_types import StrategyType

# PHI Identification DTOs | PHI 識別 DTO
from .phi_identification_models import (
    PHIDetectionResponse,
    PHIIdentificationConfig,
    PHIIdentificationResult,
)

# PHI Type Mapper | PHI 類型映射器
from .phi_type_mapper import (
    PHITypeMapper,
    get_default_mapper,
    register_custom_mappings_from_config,
)
from .phi_types import CustomPHIType, PHIType

# Value Objects | 值物件
from .value_objects import (
    DocumentMetadata,
    RegulationContext,
    SupportedLanguage,
    ValidationResult,
)

__all__ = [
    # Type Definitions
    "PHIType",
    "CustomPHIType",
    "StrategyType",
    # Entities
    "PHIEntity",
    # Value Objects
    "SupportedLanguage",
    "RegulationContext",
    "DocumentMetadata",
    "ValidationResult",
    # Aggregates
    "MedicalDocument",
    # PHI Type Mapper
    "PHITypeMapper",
    "get_default_mapper",
    "register_custom_mappings_from_config",
    # PHI Identification DTOs
    "PHIIdentificationResult",
    "PHIDetectionResponse",
    "PHIIdentificationConfig",
    # RAG Configuration Models
    "EmbeddingsConfig",
    "RegulationStoreConfig",
    "RegulationRetrieverConfig",
    "RegulationRetrievalConfig",
    "MedicalRetrieverConfig",
    # Document Loader Models
    "DocumentFormat",
    "LoaderDocumentMetadata",
    "LoadedDocument",
    "LoaderConfig",
]
