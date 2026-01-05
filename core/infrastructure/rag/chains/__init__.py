"""
PHI Identification Chain Modules
PHI 識別鏈模組

This package contains modularized components of PHI identification chain:
此套件包含 PHI 識別鏈的模組化組件：

- map_reduce: MapReduce pattern implementation (Map 和 Reduce 實現)
- processors: Core PHI identification processors (核心 PHI 識別處理器)
- utils: Utility functions and helpers (工具函數和輔助功能)
- streaming_processor: FIFO stateless chunk processing (FIFO 無狀態分塊處理)
- streaming_phi_chain: Streaming PHI detection (串流 PHI 檢測)
"""

from .map_reduce import (
    build_map_chain,
    identify_phi_with_map_reduce,
    merge_phi_results,
)
from .processors import (
    build_phi_identification_chain,
    identify_phi,
    identify_phi_structured,  # Backward compatible alias
    identify_phi_with_parser,
)
from .streaming_phi_chain import (
    PHIChunkResult,
    StreamingPHIChain,
    StreamingPHIConfig,
)
from .streaming_processor import (
    ChunkInfo,
    ChunkResult,
    ProcessingCheckpoint,
    StreamingChunkProcessor,
)
from .utils import (
    deduplicate_entities,
    get_minimal_context,
    validate_entity,
)

__all__ = [
    # MapReduce
    "build_map_chain",
    "merge_phi_results",
    "identify_phi_with_map_reduce",
    # Processors
    "identify_phi",
    "identify_phi_structured",
    "identify_phi_with_parser",
    "build_phi_identification_chain",
    # Utils
    "get_minimal_context",
    "deduplicate_entities",
    "validate_entity",
    # Streaming
    "StreamingChunkProcessor",
    "ChunkInfo",
    "ChunkResult",
    "ProcessingCheckpoint",
    "StreamingPHIChain",
    "StreamingPHIConfig",
    "PHIChunkResult",
]
