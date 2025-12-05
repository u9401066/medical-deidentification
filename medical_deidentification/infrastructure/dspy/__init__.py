"""
DSPy Integration for PHI Identification
DSPy 整合 PHI 識別

Uses DSPy for automatic prompt optimization with clear metrics:
- PHI Detection Rate (Recall)
- False Positive Rate (Precision)
- F1 Score

使用 DSPy 進行自動 prompt 優化，具有明確指標：
- PHI 檢出率 (Recall)
- 誤檢率 (Precision)
- F1 分數
"""

from .phi_module import (
    PHIIdentifier,
    PHIEntity as DSPyPHIEntity,
    parse_phi_entities,
)
from .metrics import (
    phi_precision,
    phi_recall,
    phi_f1_score,
    PHIEvaluator,
)
from .optimizer import (
    PHIPromptOptimizer,
    optimize_phi_identifier,
)

__all__ = [
    # Module
    "PHIIdentifier",
    "DSPyPHIEntity",
    "parse_phi_entities",
    
    # Metrics
    "phi_precision",
    "phi_recall", 
    "phi_f1_score",
    "PHIEvaluator",
    
    # Optimizer
    "PHIPromptOptimizer",
    "optimize_phi_identifier",
]
