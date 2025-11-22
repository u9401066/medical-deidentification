"""
LLM Configuration | LLM 配置

Centralized configuration for LLM providers.
LLM 提供者的統一配置。
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# Supported LLM providers
LLMProvider = Literal["openai", "anthropic"]

# Supported models
OPENAI_MODELS = [
    "gpt-5-nano"
    "gpt-4o",              # Latest GPT-4 Optimized (supports structured output)
    "gpt-4o-mini",        # Cost-effective GPT-4 Optimized (supports structured output)
    "gpt-4-turbo",        # GPT-4 Turbo (supports structured output)
    "gpt-4",              # Original GPT-4
    "gpt-4-turbo-preview",
    "gpt-4-1106-preview",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
]

ANTHROPIC_MODELS = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2.0",
]


class LLMConfig(BaseModel):
    """
    LLM Configuration | LLM 配置
    
    Centralized configuration for all LLM interactions.
    所有 LLM 交互的統一配置。
    
    Attributes:
        provider: LLM provider ('openai' or 'anthropic')
        model_name: Model name (e.g., 'gpt-4', 'claude-3-opus-20240229')
        temperature: Sampling temperature (0.0-1.0)
            - 0.0: Deterministic (recommended for PHI identification)
            - 1.0: Maximum creativity
        max_tokens: Maximum tokens in response (None = provider default)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
        api_key: API key (optional, defaults to env var)
        api_base: Custom API base URL (optional)
    
    Examples:
        >>> # OpenAI GPT-4 (deterministic)
        >>> config = LLMConfig(
        ...     provider="openai",
        ...     model_name="gpt-4",
        ...     temperature=0.0
        ... )
        
        >>> # Anthropic Claude 3 Opus
        >>> config = LLMConfig(
        ...     provider="anthropic",
        ...     model_name="claude-3-opus-20240229",
        ...     temperature=0.0,
        ...     max_tokens=4096
        ... )
    """
    
    provider: LLMProvider = Field(
        default="openai",
        description="LLM provider: 'openai' or 'anthropic'"
    )
    
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Model name (e.g., 'gpt-4o-mini', 'gpt-4o', 'claude-3-opus-20240229')"
    )
    
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0=deterministic, 1.0=creative)"
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum tokens in response (None=provider default)"
    )
    
    timeout: float = Field(
        default=60.0,
        ge=1.0,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for failed requests"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key (None=use environment variable)"
    )
    
    api_base: Optional[str] = Field(
        default=None,
        description="Custom API base URL (None=provider default)"
    )
    
    streaming: bool = Field(
        default=False,
        description="Enable streaming responses"
    )
    
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )
    
    def validate_model(self) -> None:
        """
        Validate model name matches provider
        
        Raises:
            ValueError: If model is not valid for provider
        """
        if self.provider == "openai":
            valid_models = OPENAI_MODELS
        elif self.provider == "anthropic":
            valid_models = ANTHROPIC_MODELS
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Allow any model name (for flexibility with new models)
        # Just warn if not in known list
        if self.model_name not in valid_models:
            import warnings
            warnings.warn(
                f"Model '{self.model_name}' not in known {self.provider} models. "
                f"Known models: {', '.join(valid_models)}"
            )
    
    def get_provider_kwargs(self) -> dict:
        """
        Get provider-specific kwargs for LangChain
        
        Returns:
            Dictionary of kwargs for ChatOpenAI or ChatAnthropic
        """
        kwargs = {
            "model": self.model_name,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "streaming": self.streaming,
            "verbose": self.verbose,
        }
        
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        
        if self.api_key is not None:
            if self.provider == "openai":
                kwargs["openai_api_key"] = self.api_key
            elif self.provider == "anthropic":
                kwargs["anthropic_api_key"] = self.api_key
        
        if self.api_base is not None:
            if self.provider == "openai":
                kwargs["openai_api_base"] = self.api_base
            # Anthropic doesn't support custom base URL in the same way
        
        return kwargs
    
    def __repr__(self) -> str:
        return f"LLMConfig(provider={self.provider}, model={self.model_name}, temp={self.temperature})"


# Preset configurations for common use cases
class LLMPresets:
    """
    Preset LLM configurations for common use cases
    常用場景的預設 LLM 配置
    """
    
    @staticmethod
    def phi_identification() -> LLMConfig:
        """
        Preset for PHI identification (deterministic, accurate)
        PHI 識別的預設配置（確定性、準確性）
        
        Uses gpt-4o-mini: supports structured output, cost-effective
        """
        return LLMConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.0,
            max_tokens=2000,
        )
    
    @staticmethod
    def regulation_analysis() -> LLMConfig:
        """
        Preset for regulation analysis (balanced)
        法規分析的預設配置（平衡性）
        
        Uses gpt-4o-mini: supports structured output, balanced quality/cost
        """
        return LLMConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.2,
            max_tokens=3000,
        )
    
    @staticmethod
    def claude_opus() -> LLMConfig:
        """
        Preset for Claude 3 Opus (highest quality)
        Claude 3 Opus 預設配置（最高品質）
        """
        return LLMConfig(
            provider="anthropic",
            model_name="claude-3-opus-20240229",
            temperature=0.0,
            max_tokens=4096,
        )
    
    @staticmethod
    def claude_sonnet() -> LLMConfig:
        """
        Preset for Claude 3 Sonnet (balanced)
        Claude 3 Sonnet 預設配置（平衡性）
        """
        return LLMConfig(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229",
            temperature=0.0,
            max_tokens=4096,
        )
    
    @staticmethod
    def gpt_4o() -> LLMConfig:
        """
        Preset for GPT-4o (highest OpenAI quality, supports structured output)
        GPT-4o 預設配置（OpenAI 最高品質，支持結構化輸出）
        """
        return LLMConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.0,
            max_tokens=4096,
        )
    
    @staticmethod
    def gpt_3_5_fast() -> LLMConfig:
        """
        Preset for GPT-3.5 (fast, economical, no structured output)
        GPT-3.5 預設配置（快速、經濟，不支持結構化輸出）
        """
        return LLMConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.0,
            max_tokens=1000,
        )
