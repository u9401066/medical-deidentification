"""
Engine Configuration
引擎配置模組

Defines configuration classes for the de-identification engine.
定義去識別化引擎的配置類別。
"""

from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from ..strategies import StrategyType
from ....domain import PHIType
from ....infrastructure.loader import LoaderConfig


class ProcessingStatus(str, Enum):
    """
    Processing status enumeration
    處理狀態枚舉
    """
    PENDING = "pending"
    LOADING = "loading"
    PROCESSING = "processing"
    MASKING = "masking"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class EngineConfig(BaseModel):
    """
    Engine configuration
    引擎配置
    
    Configures all aspects of the de-identification engine including:
    - Document loading
    - RAG (Retrieval-Augmented Generation)
    - LLM provider and model
    - Masking strategies
    - Processing options
    - Validation
    
    Examples:
        >>> config = EngineConfig(
        ...     use_rag=True,
        ...     llm_provider="openai",
        ...     llm_model="gpt-4o-mini",
        ...     default_strategy=StrategyType.GENERALIZATION
        ... )
        >>> 
        >>> # Custom PHI-specific strategies
        >>> config = EngineConfig(
        ...     phi_specific_strategies={
        ...         PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,
        ...         PHIType.NAME: StrategyType.PSEUDONYMIZATION
        ...     }
        ... )
    """
    
    # Loader configuration
    loader_config: Optional[LoaderConfig] = Field(
        default=None,
        description="Document loader configuration"
    )
    
    # RAG configuration
    use_rag: bool = Field(
        default=True,
        description="Whether to use RAG for regulation retrieval"
    )
    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai or anthropic)"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name"
    )
    embeddings_preset: str = Field(
        default="multilingual",
        description="Embeddings model preset"
    )
    
    # Masking strategy
    default_strategy: StrategyType = Field(
        default=StrategyType.REDACTION,
        description="Default masking strategy"
    )
    strategy_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy configuration"
    )
    phi_specific_strategies: Dict[PHIType, StrategyType] = Field(
        default_factory=dict,
        description="PHI-type specific strategies"
    )
    
    # Processing options
    batch_size: int = Field(
        default=10,
        description="Batch size for processing multiple documents"
    )
    parallel_processing: bool = Field(
        default=False,
        description="Enable parallel processing (future)"
    )
    
    # Validation
    validate_output: bool = Field(
        default=True,
        description="Validate output after masking"
    )
    strict_validation: bool = Field(
        default=False,
        description="Strict validation mode (fail on any PHI leakage)"
    )


__all__ = [
    "ProcessingStatus",
    "EngineConfig",
]
