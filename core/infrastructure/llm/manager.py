"""
LLM Manager | LLM 管理器

High-level interface for LLM operations with caching and retry logic.
LLM 操作的高階介面，支援快取和重試邏輯。
"""

from typing import Any

from loguru import logger

from .config import LLMConfig
from .factory import create_llm, create_structured_output_llm


class LLMManager:
    """
    LLM Manager for centralized LLM lifecycle management
    LLM 管理器，統一管理 LLM 生命週期
    
    Features:
    - Lazy initialization (LLM created only when first used)
    - Configuration management
    - Structured output support
    - Statistics tracking
    
    特性：
    - 懶載入（首次使用時才創建 LLM）
    - 配置管理
    - 結構化輸出支援
    - 統計追蹤
    
    Examples:
        >>> # Create manager with default config
        >>> manager = LLMManager()
        >>> response = manager.invoke("Translate: Hello")
        
        >>> # Use preset config
        >>> config = LLMPresets.phi_identification()
        >>> manager = LLMManager(config)
        
        >>> # Use structured output
        >>> from pydantic import BaseModel
        >>> class Answer(BaseModel):
        ...     text: str
        >>> 
        >>> response = manager.invoke_structured("What is PHI?", schema=Answer)
        >>> print(response.text)
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        auto_init: bool = False
    ):
        """
        Initialize LLM Manager
        
        Args:
            config: LLMConfig instance. Uses default if None.
            auto_init: If True, initialize LLM immediately. Otherwise lazy init.
        """
        self.config = config or LLMConfig()
        self._llm = None
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "errors": 0,
        }

        if auto_init:
            self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM instance (lazy loading)"""
        if self._llm is None:
            logger.info("Initializing LLM...")
            self._llm = create_llm(self.config)
            logger.success(f"LLM initialized: {self.config.provider}/{self.config.model_name}")

    @property
    def llm(self):
        """Get LLM instance (lazy initialization)"""
        self._initialize_llm()
        return self._llm

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke LLM with a prompt
        
        Args:
            prompt: Input prompt
            **kwargs: Additional invoke parameters
        
        Returns:
            LLM response as string
        
        Examples:
            >>> response = manager.invoke("What is HIPAA?")
        """
        self._stats["total_calls"] += 1

        try:
            logger.debug(f"Invoking LLM with prompt length: {len(prompt)}")
            response = self.llm.invoke(prompt, **kwargs)

            # Extract content based on response type
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)

            logger.debug(f"LLM response length: {len(content)}")
            return content

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"LLM invocation failed: {e}")
            raise

    def invoke_structured(
        self,
        prompt: str,
        schema,
        **kwargs
    ):
        """
        Invoke LLM with structured output
        
        Args:
            prompt: Input prompt
            schema: Pydantic model for structured output
            **kwargs: Additional invoke parameters
        
        Returns:
            Structured response (Pydantic model instance)
        
        Examples:
            >>> from pydantic import BaseModel
            >>> class PHIResult(BaseModel):
            ...     entity_text: str
            ...     phi_type: str
            >>> 
            >>> result = manager.invoke_structured(
            ...     "Find PHI: John Smith, age 92",
            ...     schema=PHIResult
            ... )
        """
        self._stats["total_calls"] += 1

        try:
            # Create LLM with structured output
            structured_llm = create_structured_output_llm(
                config=self.config,
                schema=schema
            )

            logger.debug(f"Invoking LLM with structured output: {schema.__name__}")
            response = structured_llm.invoke(prompt, **kwargs)

            logger.debug(f"Structured response: {type(response).__name__}")
            return response

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Structured LLM invocation failed: {e}")
            raise

    def batch_invoke(
        self,
        prompts: list[str],
        **kwargs
    ) -> list[str]:
        """
        Batch invoke LLM with multiple prompts
        
        Args:
            prompts: List of prompts
            **kwargs: Additional invoke parameters
        
        Returns:
            List of responses
        
        Examples:
            >>> prompts = ["Question 1", "Question 2", "Question 3"]
            >>> responses = manager.batch_invoke(prompts)
        """
        logger.info(f"Batch invoking LLM with {len(prompts)} prompts")

        responses = []
        for i, prompt in enumerate(prompts):
            logger.debug(f"Processing prompt {i+1}/{len(prompts)}")
            response = self.invoke(prompt, **kwargs)
            responses.append(response)

        logger.success(f"Batch invocation complete: {len(responses)} responses")
        return responses

    def update_config(self, **kwargs):
        """
        Update LLM configuration
        
        Args:
            **kwargs: Config parameters to update
        
        Examples:
            >>> manager.update_config(temperature=0.5)
            >>> manager.update_config(model_name="gpt-3.5-turbo")
        """
        config_dict = self.config.model_dump()
        config_dict.update(kwargs)
        self.config = LLMConfig(**config_dict)

        # Reset LLM to force re-initialization with new config
        self._llm = None
        logger.info(f"LLM config updated: {kwargs}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get LLM usage statistics
        
        Returns:
            Dictionary with statistics
        
        Examples:
            >>> stats = manager.get_stats()
            >>> print(f"Total calls: {stats['total_calls']}")
        """
        return {
            **self._stats,
            "config": self.config.model_dump(),
            "is_initialized": self._llm is not None,
        }

    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "errors": 0,
        }
        logger.info("LLM statistics reset")

    def __repr__(self) -> str:
        status = "initialized" if self._llm is not None else "not initialized"
        return (
            f"LLMManager("
            f"provider={self.config.provider}, "
            f"model={self.config.model_name}, "
            f"status={status}, "
            f"calls={self._stats['total_calls']})"
        )


# Global LLM manager instance (singleton pattern)
_global_manager: LLMManager | None = None


def get_llm_manager(
    config: LLMConfig | None = None,
    reset: bool = False
) -> LLMManager:
    """
    Get global LLM manager instance (singleton)
    獲取全域 LLM 管理器實例（單例模式）
    
    Args:
        config: LLMConfig to use for new manager. Ignored if manager exists.
        reset: If True, reset existing manager and create new one
    
    Returns:
        Global LLMManager instance
    
    Examples:
        >>> # Get default manager
        >>> manager = get_llm_manager()
        
        >>> # Get manager with custom config
        >>> config = LLMPresets.phi_identification()
        >>> manager = get_llm_manager(config)
        
        >>> # Reset and recreate
        >>> manager = get_llm_manager(reset=True)
    """
    global _global_manager

    if _global_manager is None or reset:
        if reset and _global_manager is not None:
            logger.info("Resetting global LLM manager")

        _global_manager = LLMManager(config)
        logger.info("Global LLM manager created")

    return _global_manager
