"""
LLM Factory | LLM 工廠

Factory for creating LLM instances with different providers.
創建不同提供者 LLM 實例的工廠。
"""

from typing import Union, Optional
from loguru import logger

from .config import LLMConfig, LLMProvider


def create_llm(config: Optional[LLMConfig] = None, **kwargs) -> Union['ChatOpenAI', 'ChatAnthropic']:
    """
    Create LLM instance based on configuration
    根據配置創建 LLM 實例
    
    This is the centralized factory for all LLM creation in the system.
    這是系統中所有 LLM 創建的統一工廠。
    
    Args:
        config: LLMConfig instance. If None, creates default config.
        **kwargs: Override config parameters (e.g., temperature=0.5)
    
    Returns:
        ChatOpenAI or ChatAnthropic instance
    
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


def _create_openai_llm(kwargs: dict) -> 'ChatOpenAI':
    """
    Create ChatOpenAI instance
    創建 ChatOpenAI 實例
    
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


def _create_anthropic_llm(kwargs: dict) -> 'ChatAnthropic':
    """
    Create ChatAnthropic instance
    創建 ChatAnthropic 實例
    
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


def _create_ollama_llm(kwargs: dict) -> 'ChatOllama':
    """
    Create Ollama LLM instance (local models)
    創建 Ollama LLM 實例（本地模型）
    
    Args:
        kwargs: Provider-specific kwargs
    
    Returns:
        ChatOllama instance
    
    Raises:
        ImportError: If langchain_community is not installed
    """
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError as e:
        logger.error("langchain_community not installed. Run: pip install langchain-community")
        raise ImportError(
            "langchain_community is required for Ollama models. "
            "Install with: pip install langchain-community"
        ) from e
    
    # Add Ollama-specific timeout settings
    kwargs.setdefault('timeout', 120)  # 2 minutes
    kwargs.setdefault('request_timeout', 120.0)  # 2 minutes for requests
    
    llm = ChatOllama(**kwargs)
    logger.success(f"Created ChatOllama: {kwargs.get('model', 'unknown')} (timeout={kwargs.get('timeout')}s)")
    return llm


def create_openai_llm(
    model: str = "gpt-4",
    temperature: float = 0.0,
    **kwargs
) -> 'ChatOpenAI':
    """
    Convenience function to create OpenAI LLM
    便捷函數：創建 OpenAI LLM
    
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
    **kwargs
) -> 'ChatAnthropic':
    """
    Convenience function to create Anthropic LLM
    便捷函數：創建 Anthropic LLM
    
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


def create_structured_output_llm(
    config: Optional[LLMConfig] = None,
    schema = None,
    **kwargs
):
    """
    Create LLM with structured output capability
    創建支援結構化輸出的 LLM
    
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
    
    logger.info(f"Adding structured output schema: {schema.__name__}")
    return llm.with_structured_output(schema)


# Alias for backward compatibility
create_llm_with_structured_output = create_structured_output_llm
