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

設計原則：
1. 單一真相來源：所有 prompts 定義在一處
2. 版本控制：支援多版本 prompts
3. 多語言：支援不同語言的 prompts
4. 可測試：易於測試和驗證 prompts
5. 可維護：清晰的結構和文檔
"""

from typing import Dict, Optional
from enum import Enum


class PromptType(str, Enum):
    """Prompt types in the system"""
    PHI_IDENTIFICATION = "phi_identification"
    PHI_IDENTIFICATION_STRUCTURED = "phi_identification_structured"
    PHI_VALIDATION = "phi_validation"
    MASKING_STRATEGY = "masking_strategy"


class PromptLanguage(str, Enum):
    """Supported languages for prompts"""
    ENGLISH = "en"
    CHINESE_TRADITIONAL = "zh-TW"
    CHINESE_SIMPLIFIED = "zh-CN"


# ============================================================================
# PHI Identification Prompts | PHI 識別 Prompts
# ============================================================================

PHI_IDENTIFICATION_PROMPT_V1 = """You are a medical de-identification expert. Based on the provided regulations, identify all PHI (Protected Health Information) in the given medical text.

Regulations (retrieved from vector store):
{context}

Medical Text:
{question}

Instructions:
1. Identify ALL PHI entities according to the regulations
2. For each entity, provide:
   - entity_text: The exact text from the document
   - phi_type: Type according to regulations (e.g., NAME, AGE_OVER_89, RARE_DISEASE)
   - start_position: Character position where entity starts
   - end_position: Character position where entity ends
   - confidence: Your confidence level (0.0-1.0)
   - reason: Why this is considered PHI according to regulations

3. Special attention to:
   - Ages over 89 (HIPAA Safe Harbor)
   - Ages over 90 (Taiwan regulations)
   - Rare diseases that could identify individuals
   - Genetic information
   - Small geographic areas
   
4. Return results as JSON array:
[
  {{
    "entity_text": "...",
    "phi_type": "...",
    "start_position": 123,
    "end_position": 456,
    "confidence": 0.95,
    "reason": "..."
  }},
  ...
]

If no PHI found, return empty array: []

Answer:"""


PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1 = """Based on these regulations, identify all PHI in the medical text.

Regulations:
{context}

Medical Text:
{text}

Instructions:
1. Identify ALL PHI entities according to regulations
2. Pay special attention to:
   - Ages over 89 (HIPAA) or 90 (Taiwan)
   - Rare diseases that could identify individuals
   - Specific location information
   - Names and identifiers
3. Provide entity_text, phi_type, start_position, end_position, confidence, reason
4. Return structured response with all detected entities
"""


# ============================================================================
# PHI Validation Prompts | PHI 驗證 Prompts
# ============================================================================

PHI_VALIDATION_PROMPT_V1 = """Based on the regulations below, should this entity be masked?

Entity: {entity_text}
Claimed PHI Type: {phi_type}

Regulations:
{regulations}

Answer with JSON:
{{
  "should_mask": true/false,
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}
"""


# ============================================================================
# Masking Strategy Prompts | 遮蔽策略 Prompts
# ============================================================================

MASKING_STRATEGY_PROMPT_V1 = """Based on these regulations, what is the recommended masking strategy for {phi_type}?

Regulations:
{context}

Provide:
1. Recommended masking method
2. Examples
3. Regulation reference

Answer:"""


# ============================================================================
# Chinese (Traditional) Prompts | 繁體中文 Prompts
# ============================================================================

PHI_IDENTIFICATION_PROMPT_ZH_TW = """您是一位醫療去識別化專家。根據提供的法規，識別醫療文本中所有的個人健康資訊 (PHI)。

法規（從向量資料庫檢索）：
{context}

醫療文本：
{question}

指示：
1. 根據法規識別所有 PHI 實體
2. 對每個實體提供：
   - entity_text: 文檔中的確切文字
   - phi_type: 根據法規的類型（例如：姓名、年齡超過89歲、罕見疾病）
   - start_position: 實體開始的字元位置
   - end_position: 實體結束的字元位置
   - confidence: 您的信心水準（0.0-1.0）
   - reason: 根據法規為何這被視為 PHI 的解釋

3. 特別注意：
   - 超過 89 歲的年齡（HIPAA 安全港規則）
   - 超過 90 歲的年齡（台灣法規）
   - 可能識別個人的罕見疾病
   - 遺傳資訊
   - 小型地理區域
   
4. 以 JSON 陣列格式返回結果：
[
  {{
    "entity_text": "...",
    "phi_type": "...",
    "start_position": 123,
    "end_position": 456,
    "confidence": 0.95,
    "reason": "..."
  }},
  ...
]

如果沒有找到 PHI，返回空陣列：[]

回答："""


# ============================================================================
# System Messages | 系統訊息
# ============================================================================

SYSTEM_MESSAGE_PHI_EXPERT = "You are a medical de-identification expert specializing in identifying Protected Health Information (PHI) according to HIPAA, GDPR, and other privacy regulations."

SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW = "您是一位醫療去識別化專家，專門根據 HIPAA、GDPR 和其他隱私法規識別個人健康資訊（PHI）。"

SYSTEM_MESSAGE_REGULATION_ANALYST = "You are a healthcare regulation analyst specializing in data privacy and de-identification requirements."

SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW = "您是一位醫療法規分析師，專門研究數據隱私和去識別化要求。"


# ============================================================================
# Prompt Registry | Prompt 註冊表
# ============================================================================

PROMPT_REGISTRY: Dict[str, Dict[str, str]] = {
    # PHI Identification
    "phi_identification_v1": {
        "en": PHI_IDENTIFICATION_PROMPT_V1,
        "zh-TW": PHI_IDENTIFICATION_PROMPT_ZH_TW,
    },
    "phi_identification_structured_v1": {
        "en": PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1,
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


# ============================================================================
# Prompt Accessor Functions | Prompt 存取函數
# ============================================================================

def get_prompt(
    prompt_name: str,
    language: str = "en",
    version: Optional[str] = None
) -> str:
    """
    Get prompt template by name and language
    
    Args:
        prompt_name: Name of the prompt (e.g., "phi_identification")
        language: Language code (e.g., "en", "zh-TW")
        version: Version suffix (e.g., "v1", "v2"). If None, uses latest.
    
    Returns:
        Prompt template string
    
    Raises:
        KeyError: If prompt not found
    
    Examples:
        >>> prompt = get_prompt("phi_identification", language="en", version="v1")
        >>> prompt = get_prompt("system_phi_expert", language="zh-TW")
    """
    # Build full prompt key
    if version:
        key = f"{prompt_name}_{version}"
    else:
        # Find latest version
        matching_keys = [k for k in PROMPT_REGISTRY.keys() if k.startswith(prompt_name)]
        if not matching_keys:
            raise KeyError(f"Prompt '{prompt_name}' not found")
        # Sort by version number and get latest
        key = sorted(matching_keys)[-1]
    
    # Get prompt dict
    prompt_dict = PROMPT_REGISTRY.get(key)
    if not prompt_dict:
        raise KeyError(f"Prompt '{key}' not found in registry")
    
    # Get language version
    prompt = prompt_dict.get(language)
    if not prompt:
        # Fallback to English
        prompt = prompt_dict.get("en")
        if not prompt:
            raise KeyError(f"Prompt '{key}' has no template for language '{language}' or fallback 'en'")
    
    return prompt


def get_phi_identification_prompt(
    language: str = "en",
    version: str = "v1",
    structured: bool = False
) -> str:
    """
    Get PHI identification prompt
    
    Args:
        language: Language code
        version: Prompt version
        structured: Whether to use structured output version
    
    Returns:
        Prompt template
    
    Examples:
        >>> prompt = get_phi_identification_prompt()
        >>> prompt = get_phi_identification_prompt(language="zh-TW")
        >>> prompt = get_phi_identification_prompt(structured=True)
    """
    prompt_name = "phi_identification_structured" if structured else "phi_identification"
    return get_prompt(prompt_name, language=language, version=version)


def get_phi_validation_prompt(
    language: str = "en",
    version: str = "v1"
) -> str:
    """
    Get PHI validation prompt
    
    Args:
        language: Language code
        version: Prompt version
    
    Returns:
        Prompt template
    """
    return get_prompt("phi_validation", language=language, version=version)


def get_masking_strategy_prompt(
    language: str = "en",
    version: str = "v1"
) -> str:
    """
    Get masking strategy prompt
    
    Args:
        language: Language code
        version: Prompt version
    
    Returns:
        Prompt template
    """
    return get_prompt("masking_strategy", language=language, version=version)


def get_system_message(
    role: str = "phi_expert",
    language: str = "en"
) -> str:
    """
    Get system message for LLM
    
    Args:
        role: Role type ("phi_expert" or "regulation_analyst")
        language: Language code
    
    Returns:
        System message
    
    Examples:
        >>> msg = get_system_message("phi_expert")
        >>> msg = get_system_message("regulation_analyst", language="zh-TW")
    """
    return get_prompt(f"system_{role}", language=language)


def list_available_prompts() -> Dict[str, list]:
    """
    List all available prompts
    
    Returns:
        Dictionary with prompt names and their available languages
    
    Examples:
        >>> prompts = list_available_prompts()
        >>> print(prompts)
        {
            "phi_identification_v1": ["en", "zh-TW"],
            "phi_validation_v1": ["en"],
            ...
        }
    """
    result = {}
    for key, prompt_dict in PROMPT_REGISTRY.items():
        result[key] = list(prompt_dict.keys())
    return result


# ============================================================================
# Prompt Validation | Prompt 驗證
# ============================================================================

def validate_prompt_format(prompt: str, required_vars: list) -> bool:
    """
    Validate that prompt contains all required variables
    
    Args:
        prompt: Prompt template string
        required_vars: List of required variable names
    
    Returns:
        True if all variables present, False otherwise
    
    Examples:
        >>> valid = validate_prompt_format(
        ...     "Hello {name}, you are {age} years old",
        ...     ["name", "age"]
        ... )
        >>> print(valid)  # True
    """
    for var in required_vars:
        placeholder = "{" + var + "}"
        if placeholder not in prompt:
            return False
    return True


# ============================================================================
# Default Exports | 預設導出
# ============================================================================

# For backward compatibility, export commonly used prompts directly
PHI_IDENTIFICATION_PROMPT = PHI_IDENTIFICATION_PROMPT_V1
PHI_IDENTIFICATION_STRUCTURED_PROMPT = PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1
PHI_VALIDATION_PROMPT = PHI_VALIDATION_PROMPT_V1
MASKING_STRATEGY_PROMPT = MASKING_STRATEGY_PROMPT_V1
