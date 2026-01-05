"""
Prompt Registry and Enums
Prompt 註冊表和列舉

Central registry for all prompt templates with versioning support.
"""

from enum import Enum

from .phi_prompts import (
    MASKING_STRATEGY_PROMPT_V1,
    PHI_IDENTIFICATION_PROMPT_V1,
    PHI_IDENTIFICATION_PROMPT_ZH_TW,
    PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1,
    PHI_MAP_REDUCE_PROMPT_V1,
    PHI_VALIDATION_PROMPT_V1,
)
from .system_messages import (
    SYSTEM_MESSAGE_PHI_EXPERT,
    SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW,
    SYSTEM_MESSAGE_REGULATION_ANALYST,
    SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW,
)

# ============================================================================
# Enums
# ============================================================================

class PromptType(str, Enum):
    """Prompt types in the system"""
    PHI_IDENTIFICATION = "phi_identification"
    PHI_IDENTIFICATION_STRUCTURED = "phi_identification_structured"
    PHI_VALIDATION = "phi_validation"
    MASKING_STRATEGY = "masking_strategy"
    PHI_MAP_REDUCE = "phi_map_reduce"  # For MapReduce map stage


class PromptLanguage(str, Enum):
    """Supported languages for prompts"""
    ENGLISH = "en"
    CHINESE_TRADITIONAL = "zh-TW"
    CHINESE_SIMPLIFIED = "zh-CN"


# ============================================================================
# Prompt Registry
# ============================================================================

PROMPT_REGISTRY: dict[str, dict[str, str]] = {
    # PHI Identification
    "phi_identification_v1": {
        "en": PHI_IDENTIFICATION_PROMPT_V1,
        "zh-TW": PHI_IDENTIFICATION_PROMPT_ZH_TW,
    },
    "phi_identification_structured_v1": {
        "en": PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1,
    },

    # PHI MapReduce
    "phi_map_reduce_v1": {
        "en": PHI_MAP_REDUCE_PROMPT_V1,
    },

    # PHI Validation
    "phi_validation_v1": {
        "en": PHI_VALIDATION_PROMPT_V1,
    },

    # Masking Strategy
    "masking_strategy_v1": {
        "en": MASKING_STRATEGY_PROMPT_V1,
    },

    # System Messages
    "system_phi_expert": {
        "en": SYSTEM_MESSAGE_PHI_EXPERT,
        "zh-TW": SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW,
    },
    "system_regulation_analyst": {
        "en": SYSTEM_MESSAGE_REGULATION_ANALYST,
        "zh-TW": SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW,
    },
}
