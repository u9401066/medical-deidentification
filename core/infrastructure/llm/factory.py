"""
LLM Factory | LLM 工廠

Factory for creating LLM instances with different providers.
創建不同提供者 LLM 實例的工廠。
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from loguru import logger

from .config import LLMConfig

if TYPE_CHECKING:
    from langchain_anthropic import ChatAnthropic
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI

    # Union type for all supported LLM types
    LLMType = ChatOpenAI | ChatAnthropic | ChatOllama


def create_llm(config: LLMConfig | None = None, **kwargs: Any) -> LLMType:
    """
    Create LLM instance based on configuration.
    根據配置創建 LLM 實例。

    This is the centralized factory for all LLM creation in the system.
    這是系統中所有 LLM 創建的統一工廠。

    Args:
        config: LLMConfig instance. If None, creates default config.
        **kwargs: Override config parameters (e.g., temperature=0.5)

    Returns:
        ChatOpenAI, ChatAnthropic, or ChatOllama instance

    Raises:
        ValueError: If provider is not supported
        ImportError: If provider package is not installed

    Examples:
        >>> # Use default config (OpenAI GPT-4)
        >>> llm = create_llm()

        >>> # Use preset config
        >>> from .config import LLMPresets
        >>> config = LLMPresets.phi_identification()
        >>> llm = create_llm(config)

        >>> # Override config parameters
        >>> llm = create_llm(config, temperature=0.5)

        >>> # Create from scratch
        >>> config = LLMConfig(provider="anthropic", model_name="claude-3-opus-20240229")
        >>> llm = create_llm(config)
    """
    # Create default config if not provided
    if config is None:
        config = LLMConfig()

    # Handle dict config (convert to LLMConfig)
    if isinstance(config, dict):
        config = LLMConfig(**config)

    # Override config with kwargs
    if kwargs:
        config_dict = config.model_dump()
        config_dict.update(kwargs)
        config = LLMConfig(**config_dict)

    # Validate model
    config.validate_model()

    # Log LLM creation
    logger.info(
        f"Creating LLM: provider={config.provider}, "
        f"model={config.model_name}, temperature={config.temperature}"
    )

    # Get provider-specific kwargs
    provider_kwargs = config.get_provider_kwargs()

    # Create LLM based on provider
    if config.provider == "openai":
        return _create_openai_llm(provider_kwargs)
    elif config.provider == "anthropic":
        return _create_anthropic_llm(provider_kwargs)
    elif config.provider == "ollama":
        return _create_ollama_llm(provider_kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


# =============================================================================
# Provider-specific factory functions
# =============================================================================


def _create_openai_llm(kwargs: dict[str, Any]) -> ChatOpenAI:
    """
    Create ChatOpenAI instance.
    創建 ChatOpenAI 實例。

    Args:
        kwargs: Provider-specific kwargs

    Returns:
        ChatOpenAI instance

    Raises:
        ImportError: If langchain_openai is not installed
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        logger.error("langchain_openai not installed. Run: pip install langchain-openai")
        raise ImportError(
            "langchain_openai is required for OpenAI models. "
            "Install with: pip install langchain-openai"
        ) from e

    llm = ChatOpenAI(**kwargs)
    logger.success(f"Created ChatOpenAI: {kwargs.get('model', 'unknown')}")
    return llm


def _create_anthropic_llm(kwargs: dict[str, Any]) -> ChatAnthropic:
    """
    Create ChatAnthropic instance.
    創建 ChatAnthropic 實例。

    Args:
        kwargs: Provider-specific kwargs

    Returns:
        ChatAnthropic instance

    Raises:
        ImportError: If langchain_anthropic is not installed
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        logger.error("langchain_anthropic not installed. Run: pip install langchain-anthropic")
        raise ImportError(
            "langchain_anthropic is required for Anthropic models. "
            "Install with: pip install langchain-anthropic"
        ) from e

    llm = ChatAnthropic(**kwargs)
    logger.success(f"Created ChatAnthropic: {kwargs.get('model', 'unknown')}")
    return llm


def _create_ollama_llm(kwargs: dict[str, Any]) -> ChatOllama:
    """
    Create Ollama LLM instance (local models).
    創建 Ollama LLM 實例 (本地模型)。

    Args:
        kwargs: Provider-specific kwargs

    Returns:
        ChatOllama instance

    Raises:
        ImportError: If langchain_ollama is not installed
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        logger.error("langchain-ollama not installed. Run: pip install langchain-ollama")
        raise ImportError(
            "langchain-ollama is required for Ollama models. "
            "Install with: pip install langchain-ollama"
        ) from e

    # Add Ollama-specific timeout settings
    kwargs.setdefault('timeout', 120)  # 2 minutes
    kwargs.setdefault('request_timeout', 120.0)  # 2 minutes for requests

    # GPU Configuration
    # Extract GPU settings before creating ChatOllama (these are not ChatOllama params)
    use_gpu = kwargs.pop('use_gpu', True)
    num_gpu = kwargs.pop('num_gpu', None)
    kwargs.pop('gpu_layers', None)  # Remove unused parameter

    # keep_alive controls how long model stays loaded in memory
    # This significantly reduces response latency for subsequent calls
    keep_alive = kwargs.get('keep_alive', '30m')  # Default 30 minutes

    # Configure Ollama GPU usage via environment variables
    # Ollama automatically uses GPU if available, but we can control it
    gpu_status = _configure_ollama_gpu(use_gpu, num_gpu)

    llm = ChatOllama(**kwargs)

    logger.success(
        f"Created ChatOllama: {kwargs.get('model', 'unknown')} "
        f"(timeout={kwargs.get('timeout')}s, processor={gpu_status}, "
        f"keep_alive={keep_alive}, num_ctx={kwargs.get('num_ctx', 'default')})"
    )
    return llm


def _configure_ollama_gpu(use_gpu: bool, num_gpu: int | None) -> str:
    """
    Configure Ollama GPU settings via environment variables.

    Args:
        use_gpu: Whether to use GPU
        num_gpu: Number of GPUs to use (None for auto-detect)

    Returns:
        GPU status string for logging
    """
    if not use_gpu or num_gpu == 0:
        # Force CPU-only mode
        os.environ['OLLAMA_NUM_GPU'] = '0'
        logger.info("Ollama configured for CPU-only mode")
        return "CPU-only"
    elif num_gpu is not None and num_gpu > 0:
        # Specify number of GPUs
        os.environ['OLLAMA_NUM_GPU'] = str(num_gpu)
        logger.info(f"Ollama configured to use {num_gpu} GPU(s)")
        return f"GPU x{num_gpu}"
    else:
        # Let Ollama auto-detect and use all available GPUs (default)
        logger.info("Ollama will auto-detect and use all available GPUs")
        return "GPU (auto)"


# =============================================================================
# Convenience functions
# =============================================================================


def create_openai_llm(
    model: str = "gpt-4",
    temperature: float = 0.0,
    **kwargs: Any
) -> ChatOpenAI:
    """
    Convenience function to create OpenAI LLM.
    便捷函數: 創建 OpenAI LLM。

    Args:
        model: OpenAI model name
        temperature: Sampling temperature
        **kwargs: Additional ChatOpenAI kwargs

    Returns:
        ChatOpenAI instance

    Examples:
        >>> llm = create_openai_llm("gpt-4", temperature=0.0)
        >>> llm = create_openai_llm("gpt-3.5-turbo", max_tokens=1000)
    """
    config = LLMConfig(
        provider="openai",
        model_name=model,
        temperature=temperature,
        **kwargs
    )
    return create_llm(config)


def create_anthropic_llm(
    model: str = "claude-3-opus-20240229",
    temperature: float = 0.0,
    **kwargs: Any
) -> ChatAnthropic:
    """
    Convenience function to create Anthropic LLM.
    便捷函數: 創建 Anthropic LLM。

    Args:
        model: Anthropic model name
        temperature: Sampling temperature
        **kwargs: Additional ChatAnthropic kwargs

    Returns:
        ChatAnthropic instance

    Examples:
        >>> llm = create_anthropic_llm("claude-3-opus-20240229")
        >>> llm = create_anthropic_llm("claude-3-sonnet-20240229", max_tokens=2000)
    """
    config = LLMConfig(
        provider="anthropic",
        model_name=model,
        temperature=temperature,
        **kwargs
    )
    return create_llm(config)


# =============================================================================
# Structured output utilities
# =============================================================================


def get_structured_output_method(llm: Any) -> str | None:
    """
    Get the best structured output method for the given LLM.
    根據 LLM provider 返回最佳 structured output method。

    Different providers support different methods:
    - ChatOllama: json_schema (native, most reliable)
    - ChatOpenAI: json_schema (via response_format) or function_calling
    - ChatAnthropic: function_calling only (no json_schema support!)

    不同 provider 支援不同的方法:
    - ChatOllama: json_schema (原生, 最穩定)
    - ChatOpenAI: json_schema (透過 response_format) 或 function_calling
    - ChatAnthropic: 只支援 function_calling (不支援 json_schema!)

    Args:
        llm: LangChain chat model instance

    Returns:
        Method name string or None (use provider's default)

    Examples:
        >>> from langchain_ollama import ChatOllama
        >>> llm = ChatOllama(model="qwen2.5:7b")
        >>> method = get_structured_output_method(llm)
        >>> llm.with_structured_output(MySchema, method=method)
    """
    # Get LLM type identifier
    llm_type = getattr(llm, '_llm_type', '') or ''
    class_name = llm.__class__.__name__.lower()

    # Combine for more reliable detection
    identifier = f"{llm_type} {class_name}".lower()

    if 'anthropic' in identifier or 'claude' in identifier:
        # Anthropic/Claude only supports function_calling
        # Using json_schema will raise an error
        logger.debug("Detected Anthropic/Claude LLM, using function_calling method")
        return "function_calling"

    elif 'ollama' in identifier:
        # Ollama has native JSON schema support (most reliable)
        logger.debug("Detected Ollama LLM, using json_schema method")
        return "json_schema"

    elif 'openai' in identifier or 'gpt' in identifier:
        # OpenAI supports both, json_schema is more reliable
        logger.debug("Detected OpenAI LLM, using json_schema method")
        return "json_schema"

    else:
        # Unknown provider - let LangChain use its default
        logger.debug(f"Unknown LLM type '{identifier}', using provider default")
        return None


def create_structured_output_llm(
    config: LLMConfig | None = None,
    schema: type | None = None,
    **kwargs: Any
) -> Any:
    """
    Create LLM with structured output capability.
    創建支援結構化輸出的 LLM。

    Automatically selects the best structured output method based on provider.
    根據 provider 自動選擇最佳 structured output 方法。

    Args:
        config: LLMConfig instance
        schema: Pydantic model for structured output
        **kwargs: Override config parameters

    Returns:
        LLM with structured output (.with_structured_output(schema))

    Examples:
        >>> from pydantic import BaseModel
        >>>
        >>> class Response(BaseModel):
        ...     answer: str
        ...     confidence: float
        >>>
        >>> llm = create_structured_output_llm(schema=Response)
        >>> result = llm.invoke("What is 2+2?")
        >>> print(result.answer, result.confidence)
    """
    llm = create_llm(config, **kwargs)

    if schema is None:
        logger.warning("No schema provided for structured output, returning base LLM")
        return llm

    # Auto-detect best method for this provider
    method = get_structured_output_method(llm)

    logger.info(f"Adding structured output schema: {schema.__name__} (method={method})")

    if method:
        return llm.with_structured_output(schema, method=method)
    else:
        return llm.with_structured_output(schema)


# Alias for backward compatibility
create_llm_with_structured_output = create_structured_output_llm
