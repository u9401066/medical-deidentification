"""
Prompt Accessor Functions
Prompt 存取函數

Functions to retrieve prompts by name, language, and version.
"""

from typing import Dict, Optional
import re

from .registry import PROMPT_REGISTRY


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


def get_phi_map_reduce_prompt(
    language: str = "en",
    version: str = "v1"
) -> str:
    """
    Get PHI MapReduce map stage prompt
    
    Args:
        language: Language code
        version: Prompt version
    
    Returns:
        Prompt template for MapReduce map stage
    
    Examples:
        >>> prompt = get_phi_map_reduce_prompt()
    """
    return get_prompt("phi_map_reduce", language=language, version=version)


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
            'phi_identification_v1': ['en', 'zh-TW'],
            'phi_validation_v1': ['en'],
            ...
        }
    """
    result = {}
    for key, langs in PROMPT_REGISTRY.items():
        result[key] = list(langs.keys())
    return result


def validate_prompt_format(prompt: str, required_vars: list) -> bool:
    """
    Validate that prompt contains required variables
    
    Args:
        prompt: Prompt template string
        required_vars: List of required variable names (e.g., ["context", "text"])
    
    Returns:
        True if all required variables are present
    
    Examples:
        >>> prompt = "Context: {context}\\nText: {text}"
        >>> validate_prompt_format(prompt, ["context", "text"])
        True
        >>> validate_prompt_format(prompt, ["context", "question"])
        False
    """
    # Find all variables in prompt using regex
    found_vars = re.findall(r'\{(\w+)\}', prompt)
    
    # Check if all required vars are present
    for var in required_vars:
        if var not in found_vars:
            return False
    
    return True
