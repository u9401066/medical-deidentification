"""
Domain Layer | 領域層

Contains core business logic and domain models following DDD principles.
包含遵循 DDD 原則的核心業務邏輯與領域模型。

Refactored Structure (DDD Pattern):
重構結構（領域驅動設計模式）:

This layer is framework-agnostic and organized by DDD building blocks:
此層與框架無關，按 DDD 構建塊組織：

- phi_types.py: Type definitions (PHIType enum, CustomPHIType)
  類型定義（PHIType 枚舉、自定義類型）
  
- entities.py: Domain entities with identity (PHIEntity)
  具有身份的領域實體（PHI 實體）
  
- value_objects.py: Immutable value objects (SupportedLanguage, RegulationContext, etc.)
  不可變值物件（支援語言、法規上下文等）
  
- aggregates.py: Aggregate roots (MedicalDocument)
  聚合根（醫療文件）
  
- models.py: Unified export interface (backward compatibility)
  統一導出接口（向後兼容）
"""

# Export all domain models through models.py
# 通過 models.py 導出所有領域模型
from .models import (
    # PHI Types
    PHIType,
    CustomPHIType,
    
    # Entities
    PHIEntity,
    
    # Value Objects
    SupportedLanguage,
    RegulationContext,
    DocumentMetadata,
    ValidationResult,
    
    # Aggregates
    MedicalDocument,
)

__all__ = [
    "PHIType",
    "CustomPHIType",
    "PHIEntity",
    "SupportedLanguage",
    "RegulationContext",
    "DocumentMetadata",
    "ValidationResult",
    "MedicalDocument",
]
