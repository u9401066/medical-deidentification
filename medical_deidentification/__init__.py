"""
Medical Text De-identification Toolkit | 醫療文本去識別化工具套件

A Python toolkit for automated de-identification of medical records using LLM/Agent 
technology with RAG-enhanced regulation retrieval.

基於 LLM/Agent 技術與 RAG 增強法規檢索的醫療病歷自動去識別化工具套件。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

# Core domain models (no dependencies)
from medical_deidentification.domain import (
    MedicalDocument,
    PHIEntity,
    PHIType,
    SupportedLanguage
)

# Application components (require dependencies)
try:
    from medical_deidentification.application.processing import (
        DeidentificationEngine,
        DeidentificationPipeline,
    )
    _HAS_PROCESSING = True
except ImportError:
    _HAS_PROCESSING = False
    DeidentificationEngine = None
    DeidentificationPipeline = None

__all__ = [
    "MedicalDocument",
    "PHIEntity",
    "PHIType",
    "SupportedLanguage",
    "DeidentificationEngine",
    "DeidentificationPipeline",
]
