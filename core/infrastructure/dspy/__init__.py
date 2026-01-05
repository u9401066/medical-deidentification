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

NEW in v1.1.0:
- YAML-based prompt configuration
- PHIIdentifierWithConfig for configurable prompts
- Optimization result persistence to YAML
"""

from .metrics import (
    EvaluationResult,
    PHIEvaluator,
    phi_f1_score,
    phi_precision,
    phi_recall,
)
from .optimizer import (
    OptimizationResult,
    PHIPromptOptimizer,
    load_optimized_identifier,
    # NEW: YAML integration
    optimize_and_save_to_yaml,
    optimize_phi_identifier,
)
from .phi_module import (
    LIGHTWEIGHT_MODELS,
    # Core module
    PHIIdentifier,
    # NEW: YAML-based configuration
    PHIIdentifierWithConfig,
    # Configuration
    configure_dspy_ollama,
    configure_dspy_openai,
    create_phi_identifier_from_yaml,
    parse_phi_entities,
)
from .phi_module import (
    PHIEntity as DSPyPHIEntity,
)

__all__ = [
    # Core Module
    "PHIIdentifier",
    "DSPyPHIEntity",
    "parse_phi_entities",

    # Configuration
    "configure_dspy_ollama",
    "configure_dspy_openai",
    "LIGHTWEIGHT_MODELS",

    # NEW: YAML-based Configuration
    "PHIIdentifierWithConfig",
    "create_phi_identifier_from_yaml",

    # Metrics
    "phi_precision",
    "phi_recall",
    "phi_f1_score",
    "PHIEvaluator",
    "EvaluationResult",

    # Optimizer
    "PHIPromptOptimizer",
    "OptimizationResult",
    "optimize_phi_identifier",

    # NEW: YAML Integration
    "optimize_and_save_to_yaml",
    "load_optimized_identifier",
]
