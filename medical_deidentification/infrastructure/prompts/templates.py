"""
Prompt Templates for RAG System | RAG 系統的 Prompt 模板

Centralized management of all prompt templates used in the medical
de-identification system.

集中管理醫療去識別化系統中使用的所有 prompt 模板。

Design Principles:
1. Single Source of Truth: All prompts defined in one place
2. Versioning: Support multiple versions of prompts
3. Multilingual: Support prompts in different languages
4. Testable: Easy to test and validate prompts
5. Maintainable: Clear structure and documentation
6. Modular: Prompts organized by category in separate files

設計原則：
1. 單一真相來源：所有 prompts 定義在一處
2. 版本控制：支援多版本 prompts
3. 多語言：支援不同語言的 prompts
4. 可測試：易於測試和驗證 prompts
5. 可維護：清晰的結構和文檔
6. 模組化：Prompts 按類別組織在獨立檔案

Module Structure:
- phi_prompts.py: PHI identification, validation, and masking prompts
- system_messages.py: System messages and default contexts
- registry.py: Central prompt registry with enums
- accessors.py: Functions to retrieve prompts
- templates.py: Main entry point (this file)
"""

# Re-export all components from submodules
from .phi_prompts import (
    # Versioned prompts
    PHI_IDENTIFICATION_PROMPT_V1,
    PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1,
    PHI_IDENTIFICATION_PROMPT_ZH_TW,
    PHI_VALIDATION_PROMPT_V1,
    MASKING_STRATEGY_PROMPT_V1,
    PHI_MAP_REDUCE_PROMPT_V1,
    
    # Backward compatibility aliases
    PHI_IDENTIFICATION_PROMPT,
    PHI_IDENTIFICATION_STRUCTURED_PROMPT,
    PHI_VALIDATION_PROMPT,
    MASKING_STRATEGY_PROMPT,
)

from .system_messages import (
    # System messages
    SYSTEM_MESSAGE_PHI_EXPERT,
    SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW,
    SYSTEM_MESSAGE_REGULATION_ANALYST,
    SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW,
    
    # Default contexts
    DEFAULT_HIPAA_SAFE_HARBOR_RULES,
)

from .registry import (
    # Enums
    PromptType,
    PromptLanguage,
    
    # Registry
    PROMPT_REGISTRY,
)

from .accessors import (
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
    
    # Versioned prompts
    "PHI_IDENTIFICATION_PROMPT_V1",
    "PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1",
    "PHI_IDENTIFICATION_PROMPT_ZH_TW",
    "PHI_VALIDATION_PROMPT_V1",
    "MASKING_STRATEGY_PROMPT_V1",
    "PHI_MAP_REDUCE_PROMPT_V1",
    
    # Backward compatibility aliases
    "PHI_IDENTIFICATION_PROMPT",
    "PHI_IDENTIFICATION_STRUCTURED_PROMPT",
    "PHI_VALIDATION_PROMPT",
    "MASKING_STRATEGY_PROMPT",
    
    # System messages
    "SYSTEM_MESSAGE_PHI_EXPERT",
    "SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW",
    "SYSTEM_MESSAGE_REGULATION_ANALYST",
    "SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW",
    
    # Default contexts
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
