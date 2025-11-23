"""
Module 3: Core Processing Engine | 核心處理引擎

Orchestrates the complete de-identification workflow:
1. Load documents (Module 1)
2. Retrieve regulations via RAG (Module 2)
3. Identify PHI using LLM
4. Apply masking strategies (Module 5)
5. Validate and return results

編排完整的去識別化工作流程：
1. 載入文件（模組 1）
2. 透過 RAG 檢索法規（模組 2）
3. 使用 LLM 識別 PHI
4. 應用遮蔽策略（模組 5）
5. 驗證並返回結果
"""

from .engine import (
    DeidentificationEngine,
    EngineConfig,
    ProcessingResult,
    ProcessingStatus
)

from .pipeline import (
    DeidentificationPipeline,
    PipelineStage,
    StageResult
)

from .context import (
    ProcessingContext,
    DocumentContext,
    RegulationContext
)

from ...domain import StrategyType
from .strategies import (
    MaskingStrategy,
    RedactionStrategy,
    GeneralizationStrategy,
    PseudonymizationStrategy,
    DateShiftingStrategy,
    PartialMaskingStrategy,
    SuppressionStrategy,
    create_masking_strategy,
    get_default_strategy_for_phi_type
)

from .batch_processor import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    BatchProcessingResult,
    RowProcessingResult,
    save_batch_results
)

from .output_manager import (
    OutputManager,
    OutputConfig,
    get_default_output_manager,
    set_default_output_manager,
    get_result_path,
    get_report_path
)

from .report_generator import (
    ReportGenerator,
    generate_batch_report,
    save_batch_report
)

__all__ = [
    # Engine
    "DeidentificationEngine",
    "EngineConfig",
    "ProcessingResult",
    "ProcessingStatus",
    
    # Pipeline
    "DeidentificationPipeline",
    "PipelineStage",
    "StageResult",
    
    # Context
    "ProcessingContext",
    "DocumentContext",
    "RegulationContext",
    
    # Strategies
    "MaskingStrategy",
    "StrategyType",
    "RedactionStrategy",
    "GeneralizationStrategy",
    "PseudonymizationStrategy",
    "DateShiftingStrategy",
    "PartialMaskingStrategy",
    "SuppressionStrategy",
    "create_masking_strategy",
    "get_default_strategy_for_phi_type",
    
    # Batch Processing
    "BatchPHIProcessor",
    "BatchProcessingConfig",
    "BatchProcessingResult",
    "RowProcessingResult",
    "save_batch_results",
    
    # Output Management
    "OutputManager",
    "OutputConfig",
    "get_default_output_manager",
    "set_default_output_manager",
    "get_result_path",
    "get_report_path",
    
    # Report Generation
    "ReportGenerator",
    "generate_batch_report",
    "save_batch_report",
]
