"""
Domain Models | 領域模型

Core domain entities and value objects for medical document de-identification.
醫療文件去識別化的核心領域實體與值物件。

Refactored Structure (DDD Pattern):
重構結構（領域驅動設計模式）:

├── phi_types.py        - PHI type definitions (PHIType enum, CustomPHIType)
│                        PHI 類型定義（PHIType 枚舉、自定義類型）
│
├── entities.py         - Domain entities (PHIEntity)
│                        領域實體（PHI 實體）
│
├── value_objects.py    - Value objects (SupportedLanguage, RegulationContext, etc.)
│                        值物件（支援語言、法規上下文等）
│
├── aggregates.py       - Aggregate roots (MedicalDocument)
│                        聚合根（醫療文件）
│
└── models.py (this)    - Unified export interface
                         統一導出接口（向後兼容）

Benefits of this refactoring:
重構的好處：
- Separation of Concerns: Each file has a single responsibility
  關注點分離：每個檔案都有單一職責
  
- DDD Alignment: Clear distinction between entities, value objects, and aggregates
  符合 DDD：實體、值物件和聚合之間有明確區分
  
- Maintainability: Easier to locate and modify specific domain concepts
  可維護性：更容易定位和修改特定領域概念
  
- Testability: Can test each component independently
  可測試性：可以獨立測試每個組件
  
- Backward Compatibility: All existing imports still work
  向後兼容：所有現有的導入仍然有效
"""

# Re-export all domain models for backward compatibility
# 重新導出所有領域模型以保持向後兼容
from .phi_types import PHIType, CustomPHIType
from .entities import PHIEntity
from .value_objects import (
    SupportedLanguage,
    RegulationContext,
    DocumentMetadata,
    ValidationResult
)
from .aggregates import MedicalDocument

# PHI Identification Models (DTOs for LLM structured output)
# PHI 識別模型（LLM 結構化輸出的 DTO）
from .phi_identification_models import (
    PHIIdentificationResult,
    PHIDetectionResponse,
    PHIIdentificationConfig,
)

__all__ = [
    # PHI Types | PHI 類型
    "PHIType",
    "CustomPHIType",
    
    # Entities | 實體
    "PHIEntity",
    
    # Value Objects | 值物件
    "SupportedLanguage",
    "RegulationContext",
    "DocumentMetadata",
    "ValidationResult",
    
    # Aggregates | 聚合
    "MedicalDocument",
    
    # PHI Identification Models | PHI 識別模型
    "PHIIdentificationResult",
    "PHIDetectionResponse",
    "PHIIdentificationConfig",
]
