"""
PHI Identification Prompts
PHI 識別 Prompts

All prompts related to PHI identification, structured output, and validation.
"""

from core.domain.phi_type_registry import get_phi_type_registry


def get_dynamic_phi_types_prompt(format: str = "list") -> str:
    """
    Get dynamic PHI types list for prompts.
    取得動態 PHI 類型列表用於 prompt。

    This function retrieves all registered PHI types from the central registry,
    including base types, custom types, RAG-discovered types, and LLM-discovered types.

    Args:
        format: Output format - "list", "json", or "markdown"

    Returns:
        Formatted string of PHI types for inclusion in prompts

    Example:
        >>> types_prompt = get_dynamic_phi_types_prompt("list")
        >>> full_prompt = f\"\"\"
        ... PHI Types to identify:
        ... {types_prompt}
        ... \"\"\"
    """
    registry = get_phi_type_registry()
    return registry.get_types_for_prompt(format=format)


def get_phi_identification_prompt_dynamic(
    context: str = "",
    text: str = "",
    include_custom_types: bool = True,
) -> str:
    """
    Generate PHI identification prompt with dynamic type list.
    生成包含動態類型列表的 PHI 識別 prompt。

    Args:
        context: Regulation context
        text: Medical text to analyze
        include_custom_types: Whether to include custom/discovered types

    Returns:
        Complete prompt with dynamic type list
    """
    registry = get_phi_type_registry()
    types_section = registry.get_types_for_prompt(
        format="list",
        include_base=True,
        include_custom=include_custom_types,
    )

    return f"""You are a PHI identification expert. Identify all Protected Health Information (PHI) in the medical text according to regulations.

═══════════════════════════════════════════════════════════════════════════════
KNOWN PHI TYPES (標準 + 自訂 PHI 類型)
═══════════════════════════════════════════════════════════════════════════════
{types_section}

NOTE: If you discover a PHI type not listed above, use format: "CUSTOM:YOUR_TYPE_NAME"
注意：如果發現上列未包含的 PHI 類型，請使用格式：「CUSTOM:自訂類型名稱」

═══════════════════════════════════════════════════════════════════════════════
REGULATIONS (法規)
═══════════════════════════════════════════════════════════════════════════════
{context}

═══════════════════════════════════════════════════════════════════════════════
MEDICAL TEXT TO ANALYZE (待分析醫療文本)
═══════════════════════════════════════════════════════════════════════════════
{text}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS (指示)
═══════════════════════════════════════════════════════════════════════════════
1. Identify ALL PHI entities according to regulations
2. For each entity, provide:
   - entity_text: Exact text from document
   - phi_type: Type from the list above (or CUSTOM:xxx for new types)
   - start_position: Character position where entity starts
   - end_position: Character position where entity ends
   - confidence: Your confidence level (0.0-1.0)
   - reason: Explanation of why this is PHI

3. Special rules:
   - Ages over 89 years ONLY (ages 89 and below are NOT PHI)
   - Rare diseases (prevalence <1:2000) that could identify individuals
   - Common diseases like diabetes, hypertension, cancer do NOT need redaction

4. Return in structured format with all identified entities

IMPORTANT: Return ONLY the PHI entities found, NOT the full text."""

# ============================================================================
# PHI Identification Prompts (English)
# ============================================================================

PHI_IDENTIFICATION_PROMPT_V1 = """You are a data redaction assistant. Extract identifiable information from medical text for data anonymization purposes.

Privacy Protection Guidelines:
{context}

Medical Text to Analyze:
{question}

Task: Extract ALL identifiable information that should be redacted, including:
1. Personal names
2. Ages ONLY if >90 years (ages 90 and below should NOT be identified)
3. Geographic locations smaller than state level
4. Contact information (phone, email, address)
5. ID numbers and account numbers
6. Rare diseases with prevalence <1:2000 that could identify individuals (common diseases like diabetes, hypertension, cancer do NOT need redaction)
7. Genetic information
8. Dates related to individuals

For each item found, provide:
- entity_text: Exact text from document
- phi_type: Category (NAME, AGE_OVER_89, LOCATION, PHONE, EMAIL, RARE_DISEASE, GENETIC_INFO, etc.)
- start_position: Character position where it starts
- end_position: Character position where it ends
- confidence: 0.0-1.0
- reason: Why this needs redaction

Return as JSON array:
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

If nothing needs redaction, return: []

Answer:"""


PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1 = """Based on these regulations, identify all PHI in the medical text.

Regulations:
{context}

Medical Text:
{text}

Instructions:
1. Identify ALL PHI entities according to regulations
2. Pay special attention to:
   - Ages over 90 years ONLY (ages 90 and below are NOT PHI)
   - Rare diseases (prevalence <1:2000) that could identify individuals
   - Common diseases like diabetes, hypertension, cancer do NOT need redaction
   - Genetic information
   - Small geographic areas
3. For each entity, provide:
   - entity_text: Exact text from document
   - phi_type: Type according to regulations (e.g., NAME, AGE_OVER_89, RARE_DISEASE)
   - start_position: Character position where entity starts
   - end_position: Character position where entity ends
   - confidence: Your confidence level (0.0-1.0)
   - reason: Explanation of why this is PHI according to regulations

4. Return in structured format with all identified entities

IMPORTANT: Return ONLY the PHI entities found, NOT the full text."""


# ============================================================================
# PHI Identification Prompts (Chinese Traditional)
# ============================================================================

PHI_IDENTIFICATION_PROMPT_ZH_TW = """您是一位醫療去識別化專家。根據提供的法規，識別醫療文本中所有的個人健康資訊 (PHI)。

法規上下文：
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
   - 只有超過 90 歲的年齡才需要去識別化（90 歲及以下不需要）
   - 罕見疾病（發生率 <1:2000）才需要去識別化（常見疾病如糖尿病、高血壓、癌症不需要）
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
# PHI Validation Prompts
# ============================================================================

PHI_VALIDATION_PROMPT_V1 = """Validate whether the identified entity is actually PHI according to regulations.

Entity: {entity_text}
Claimed PHI Type: {phi_type}

Relevant Regulations:
{regulations}

Determine:
1. should_mask: Is this actually PHI that should be masked? (true/false)
2. confidence: How confident are you? (0.0-1.0)
3. reason: Why or why not?

Return JSON:
{{
  "should_mask": true/false,
  "confidence": 0.95,
  "reason": "..."
}}"""


# ============================================================================
# Masking Strategy Prompts
# ============================================================================

MASKING_STRATEGY_PROMPT_V1 = """Based on these regulations, recommend a masking strategy for the PHI entity.

Entity: {entity_text}
PHI Type: {phi_type}

Relevant Regulations:
{regulations}

Recommend:
1. strategy: Best masking approach (REDACT, GENERALIZE, PSEUDONYMIZE, DATE_SHIFT, etc.)
2. replacement: Suggested replacement text (if applicable)
3. rationale: Why this strategy is appropriate

Return JSON:
{{
  "strategy": "...",
  "replacement": "...",
  "rationale": "..."
}}"""


# ============================================================================
# MapReduce Map Stage Prompt
# ============================================================================

PHI_MAP_REDUCE_PROMPT_V1 = """You are a PHI identification expert.
Extract ONLY PHI entities from the medical text section, not the full text.

Identify these PHI types:
- Names (patients, doctors, family members)
- Dates (birth, admission, discharge, death)
- Locations (addresses, cities, hospital names)
- Contact info (phone, email, fax)
- IDs (SSN, medical record number, account numbers)
- Ages over 89 years

Medical Text Section:
{page_content}

Return ONLY the PHI entities found."""


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

PHI_IDENTIFICATION_PROMPT = PHI_IDENTIFICATION_PROMPT_V1
PHI_IDENTIFICATION_STRUCTURED_PROMPT = PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1
PHI_VALIDATION_PROMPT = PHI_VALIDATION_PROMPT_V1
MASKING_STRATEGY_PROMPT = MASKING_STRATEGY_PROMPT_V1
