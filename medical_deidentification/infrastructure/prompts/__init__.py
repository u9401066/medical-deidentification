"""
Prompt Management Module | Prompt 管理模組

Centralized management of all prompt templates for the medical
de-identification system.

集中管理醫療去識別化系統的所有 prompt 模板。

This module provides:
- Prompt templates for PHI identification
- Prompt templates for validation
- Multilingual support
- Version management
- Easy access functions

Examples:
    >>> # Get PHI identification prompt
    >>> from medical_deidentification.infrastructure.prompts import (
    ...     get_phi_identification_prompt
    ... )
    >>> 
    >>> prompt = get_phi_identification_prompt()
    >>> 
    >>> # Get Chinese version
    >>> prompt_zh = get_phi_identification_prompt(language="zh-TW")
    >>> 
    >>> # Get structured output version
    >>> prompt_structured = get_phi_identification_prompt(structured=True)
    
    >>> # List all available prompts
    >>> from medical_deidentification.infrastructure.prompts import (
    ...     list_available_prompts
    ... )
    >>> 
    >>> prompts = list_available_prompts()
    >>> print(prompts)
"""

from .templates import (
    # Enums
    PromptType,
    PromptLanguage,
    
    # Direct prompt access (for backward compatibility)
    PHI_IDENTIFICATION_PROMPT,
    PHI_IDENTIFICATION_STRUCTURED_PROMPT,
    PHI_VALIDATION_PROMPT,
    MASKING_STRATEGY_PROMPT,
    PHI_MAP_REDUCE_PROMPT_V1,
    
    # System messages
    SYSTEM_MESSAGE_PHI_EXPERT,
    SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW,
    SYSTEM_MESSAGE_REGULATION_ANALYST,
    SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW,
    
    # Versioned prompts
    PHI_IDENTIFICATION_PROMPT_V1,
    PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1,
    PHI_VALIDATION_PROMPT_V1,
    MASKING_STRATEGY_PROMPT_V1,
    PHI_IDENTIFICATION_PROMPT_ZH_TW,
    
    # Default regulation contexts
    DEFAULT_HIPAA_SAFE_HARBOR_RULES,
    
    # Registry
    PROMPT_REGISTRY,
    
    # Accessor functions
    get_prompt,
    get_phi_identification_prompt,
    get_phi_validation_prompt,
    get_masking_strategy_prompt,
    get_phi_map_reduce_prompt,
    get_system_message,
    list_available_prompts,
    validate_prompt_format,
)


__all__ = [
    # Enums
    "PromptType",
    "PromptLanguage",
    
    # Direct prompt access
    "PHI_IDENTIFICATION_PROMPT",
    "PHI_IDENTIFICATION_STRUCTURED_PROMPT",
    "PHI_VALIDATION_PROMPT",
    "MASKING_STRATEGY_PROMPT",
    "PHI_MAP_REDUCE_PROMPT_V1",
    
    # System messages
    "SYSTEM_MESSAGE_PHI_EXPERT",
    "SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW",
    "SYSTEM_MESSAGE_REGULATION_ANALYST",
    "SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW",
    
    # Versioned prompts
    "PHI_IDENTIFICATION_PROMPT_V1",
    "PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1",
    "PHI_VALIDATION_PROMPT_V1",
    "MASKING_STRATEGY_PROMPT_V1",
    "PHI_IDENTIFICATION_PROMPT_ZH_TW",
    
    # Default regulation contexts
    "DEFAULT_HIPAA_SAFE_HARBOR_RULES",
    
    # Registry
    "PROMPT_REGISTRY",
    
    # Accessor functions
    "get_prompt",
    "get_phi_identification_prompt",
    "get_phi_validation_prompt",
    "get_masking_strategy_prompt",
    "get_phi_map_reduce_prompt",
    "get_system_message",
    "list_available_prompts",
    "validate_prompt_format",
]
