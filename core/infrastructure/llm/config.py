"""
LLM Configuration | LLM 配置

Centralized configuration for LLM providers.
LLM 提供者的統一配置。
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# Supported LLM providers
LLMProvider = Literal["openai", "anthropic", "ollama"]

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

# Ollama local models (commonly available)
OLLAMA_MODELS = [
    "granite4:1b",     # Recommended: F1=89.4% for PHI detection
    "qwen2.5:1.5b",
    "qwen2.5:7b",
    "qwen2.5:14b",
    "llama3.2:1b",
    "llama3.2:3b",
    "llama3.1:8b",
    "smollm2:360m",
    "mistral:7b",
    "gemma2:9b",
]

# MiniMind local models (ultra-lightweight, good for resource-constrained environments)
# MiniMind 本地模型（超輕量，適合資源受限環境）
# Source: https://github.com/jingyaogong/minimind
MINIMIND_MODELS = [
    "jingyaogong/minimind2",           # Default MiniMind2 (0.1B, 104M params)
    "jingyaogong/minimind2-small",     # Small version (0.02B, 26M params)
    "jingyaogong/minimind2-moe",       # MoE version (0.15B, 145M params)
    "jingyaogong/minimind2-r1",        # Reasoning version (R1-distilled)
    "jingyaogong/minimind2-small-r1",  # Small reasoning version
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
    
    # GPU/Hardware Acceleration Settings (for Ollama and local models)
    use_gpu: bool = Field(
        default=True,
        description="Enable GPU acceleration (for Ollama and local models)"
    )
    
    num_gpu: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of GPUs to use (None = auto-detect all, 0 = CPU only, 1+ = specific count)"
    )
    
    gpu_layers: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of model layers to offload to GPU (None = all layers, 0 = CPU only)"
    )
    
    # Ollama keep_alive: How long to keep model loaded in memory
    # Ollama keep_alive: 模型在記憶體中保持載入的時間
    keep_alive: Optional[str] = Field(
        default="30m",
        description="How long to keep model loaded (e.g., '5m', '1h', '-1' for forever). Ollama only."
    )
    
    # Ollama num_ctx: Context window size
    # Ollama num_ctx: 上下文窗口大小
    num_ctx: Optional[int] = Field(
        default=8192,
        ge=512,
        description="Context window size for Ollama models (default: 8192)"
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
        elif self.provider == "ollama":
            # Combine standard Ollama models and MiniMind models
            valid_models = OLLAMA_MODELS + MINIMIND_MODELS
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
            Dictionary of kwargs for ChatOpenAI, ChatAnthropic, or ChatOllama
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
            kwargs["max_tokens"] = self.max_tokens if self.provider != "ollama" else self.max_tokens
            # Ollama uses num_predict instead of max_tokens
            if self.provider == "ollama":
                kwargs["num_predict"] = self.max_tokens
                del kwargs["max_tokens"]
        
        if self.api_key is not None:
            if self.provider == "openai":
                kwargs["openai_api_key"] = self.api_key
            elif self.provider == "anthropic":
                kwargs["anthropic_api_key"] = self.api_key
            # Ollama doesn't require API key
        
        if self.api_base is not None:
            if self.provider == "openai":
                kwargs["openai_api_base"] = self.api_base
            elif self.provider == "ollama":
                kwargs["base_url"] = self.api_base
            # Anthropic doesn't support custom base URL in the same way
        elif self.provider == "ollama":
            # Default Ollama base URL
            kwargs["base_url"] = "http://localhost:11434"
        
        # Add GPU configuration for Ollama
        if self.provider == "ollama":
            kwargs["use_gpu"] = self.use_gpu
            if self.num_gpu is not None:
                kwargs["num_gpu"] = self.num_gpu
            if self.gpu_layers is not None:
                kwargs["gpu_layers"] = self.gpu_layers
            # Keep model loaded in memory (reduces cold start latency)
            if self.keep_alive is not None:
                kwargs["keep_alive"] = self.keep_alive
            # Context window size
            if self.num_ctx is not None:
                kwargs["num_ctx"] = self.num_ctx
        
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
        
        Uses granite4:1b: local model, F1=89.4%, no API cost
        """
        return LLMConfig(
            provider="ollama",
            model_name="granite4:1b",
            temperature=0.0,
            max_tokens=2048,
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
    
    @staticmethod
    def local_granite() -> LLMConfig:
        """
        Preset for local Granite4 1B (recommended, F1=89.4%)
        本地 Granite4 1B 預設配置（推薦，F1=89.4%）
        
        Best balance of accuracy and speed for PHI detection.
        """
        return LLMConfig(
            provider="ollama",
            model_name="granite4:1b",
            temperature=0.0,
            max_tokens=2048,
        )
    
    @staticmethod
    def local_qwen() -> LLMConfig:
        """
        Preset for local Qwen 2.5 1.5B (lightweight alternative)
        本地 Qwen 2.5 1.5B 預設配置（輕量替代）
        """
        return LLMConfig(
            provider="ollama",
            model_name="qwen2.5:1.5b",
            temperature=0.0,
            max_tokens=2048,
        )
    
    @staticmethod
    def local_llama() -> LLMConfig:
        """
        Preset for local Llama 3.1 8B (local inference)
        本地 Llama 3.1 8B 預設配置（本地推理）
        """
        return LLMConfig(
            provider="ollama",
            model_name="llama3.1:8b",
            temperature=0.0,
            max_tokens=2048,
        )
    
    @staticmethod
    def local_minimind() -> LLMConfig:
        """
        Preset for local MiniMind2 (best performance, ~104M params)
        本地 MiniMind2 預設配置（效能最佳，約 104M 參數）
        
        MiniMind2 is the recommended default - best balance of quality and speed.
        Still ultra-lightweight compared to typical LLMs (GPT-3 is ~17000x larger).
        
        Ideal for:
        - Default local LLM for PHI identification
        - Low resource environments
        - Quick local experiments
        - Edge deployment scenarios
        
        Source: https://github.com/jingyaogong/minimind
        
        Note: First run will pull the model via `ollama pull jingyaogong/minimind2`
        """
        return LLMConfig(
            provider="ollama",
            model_name="jingyaogong/minimind2",
            temperature=0.0,
            max_tokens=1024,  # MiniMind trained with 512 context, extended to 1024
            use_gpu=True,     # Enables GPU if available, falls back to CPU
        )
    
    @staticmethod
    def local_minimind_small() -> LLMConfig:
        """
        Preset for local MiniMind2-Small (smallest, ~26M params)
        本地 MiniMind2-Small 預設配置（最小，約 26M 參數）
        
        The smallest MiniMind variant - can run on almost any hardware.
        Trade-off: Less capable but extremely fast and lightweight.
        
        Ideal for:
        - Extremely resource-constrained environments
        - Raspberry Pi or similar edge devices
        - Quick prototyping and testing
        """
        return LLMConfig(
            provider="ollama",
            model_name="jingyaogong/minimind2-small",
            temperature=0.0,
            max_tokens=512,
            use_gpu=True,
        )
    
    @staticmethod
    def local_minimind_reasoning() -> LLMConfig:
        """
        Preset for local MiniMind2-R1 (reasoning capability)
        本地 MiniMind2-R1 預設配置（推理能力版）
        
        MiniMind with reasoning capabilities distilled from DeepSeek-R1.
        Uses <think>...</think><answer>...</answer> format.
        
        Note: Slightly higher temperature for reasoning exploration.
        """
        return LLMConfig(
            provider="ollama",
            model_name="jingyaogong/minimind2-r1",
            temperature=0.1,  # Slightly higher for reasoning
            max_tokens=1024,
            use_gpu=True,
        )
