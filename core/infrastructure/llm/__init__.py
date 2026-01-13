"""
Module 4: LLM Integration Layer | LLM 串接層

Centralized LLM management with support for multiple providers.
統一的 LLM 管理，支援多種提供者。

This module provides:
- LLMConfig: Configuration for LLM providers
- LLMFactory: Factory for creating LLM instances
- LLMManager: High-level manager for LLM lifecycle
- LLMPresets: Preset configurations for common use cases

Examples:
    >>> # Quick start with factory
    >>> from core.infrastructure.llm import create_llm, LLMConfig
    >>> 
    >>> config = LLMConfig(provider="openai", model_name="gpt-4")
    >>> llm = create_llm(config)
    >>> 
    >>> # Use manager for advanced features
    >>> from core.infrastructure.llm import LLMManager
    >>> 
    >>> manager = LLMManager(config)
    >>> response = manager.invoke("What is HIPAA?")
    >>> 
    >>> # Use presets
    >>> from core.infrastructure.llm import LLMPresets
    >>> 
    >>> config = LLMPresets.phi_identification()
    >>> llm = create_llm(config)
"""

# Configuration
from .config import (
    ANTHROPIC_MODELS,
    MINIMIND_MODELS,
    OLLAMA_MODELS,
    OPENAI_MODELS,
    LLMConfig,
    LLMPresets,
    LLMProvider,
)

# Factory
from .factory import (
    create_anthropic_llm,
    create_llm,
    create_llm_with_structured_output,
    create_openai_llm,
    create_structured_output_llm,
    get_structured_output_method,
)

# Manager
from .manager import (
    LLMManager,
    get_llm_manager,
)

__all__ = [
    # Configuration
    "LLMConfig",
    "LLMProvider",
    "LLMPresets",
    "OPENAI_MODELS",
    "ANTHROPIC_MODELS",
    "OLLAMA_MODELS",
    "MINIMIND_MODELS",

    # Factory
    "create_llm",
    "create_openai_llm",
    "create_anthropic_llm",
    "create_structured_output_llm",
    "create_llm_with_structured_output",
    "get_structured_output_method",

    # Manager
    "LLMManager",
    "get_llm_manager",
]
