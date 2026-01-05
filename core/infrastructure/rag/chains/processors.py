"""
PHI Identification Processors using LangChain
PHI 識別處理器使用 LangChain

Core processors for PHI identification using LangChain:
- with_structured_output: Primary method using LangChain structured output
- PydanticOutputParser: Fallback for models that don't support structured output

Design Principles:
- Use LangChain tools, NOT reinvent the wheel
- LangChain fail = report error (no manual JSON parsing)
- Keep DSPy integration point for future optimization

Phase 1 Enhancement:
- Support tool_results from pre-scanning tools (regex, ID validator, etc.)
- Tool results provide hints to LLM for more accurate identification
"""

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from loguru import logger

from ....domain import PHIEntity
from ....domain.phi_identification_models import (
    PHIDetectionResponse,
    PHIIdentificationResult,
)
from ...prompts import get_phi_identification_prompt, get_system_message

# Import tool result type for type hints
from ...tools.base_tool import ToolResult


def format_tool_hints(tool_results: list[ToolResult]) -> str:
    """
    Format tool results as hints for LLM prompt
    將工具結果格式化為 LLM 提示的提示
    
    Args:
        tool_results: Pre-scanning tool results
        
    Returns:
        Formatted hint string for LLM prompt
    """
    if not tool_results:
        return ""

    # Group results by PHI type
    grouped: dict[str, list[ToolResult]] = {}
    for result in tool_results:
        phi_type = result.phi_type.value if hasattr(result.phi_type, 'value') else str(result.phi_type)
        if phi_type not in grouped:
            grouped[phi_type] = []
        grouped[phi_type].append(result)

    # Format as hints
    lines = ["[Pre-scan Tool Hints / 預掃描工具提示]"]
    lines.append("The following patterns were detected by fast scanning tools:")
    lines.append("以下模式由快速掃描工具檢測到：")
    lines.append("")

    for phi_type, results in grouped.items():
        # Deduplicate by text
        unique_texts = list(set(r.text for r in results))
        max_conf = max(r.confidence for r in results)

        lines.append(f"- {phi_type} (confidence {max_conf:.0%}): {', '.join(unique_texts[:5])}")
        if len(unique_texts) > 5:
            lines.append(f"  ... and {len(unique_texts) - 5} more")

    lines.append("")
    lines.append("Please verify these detections and identify any additional PHI.")
    lines.append("請驗證這些檢測並識別任何額外的 PHI。")

    return "\n".join(lines)


def build_phi_identification_chain(
    llm,
    language: str | None = None,
    use_structured_output: bool = True
) -> Runnable:
    """
    Build PHI identification chain using LangChain
    使用 LangChain 構建 PHI 識別 chain
    
    Uses LangChain with_structured_output or PydanticOutputParser
    使用 LangChain with_structured_output 或 PydanticOutputParser
    
    Args:
        llm: Language model
        language: Language code (optional)
        use_structured_output: Whether to use with_structured_output (True) 
                               or PydanticOutputParser (False)
        
    Returns:
        LangChain Runnable that takes {"context": str, "text": str}
        and outputs PHIDetectionResponse
    """
    system_message = get_system_message("phi_expert", language=language or "en")

    if use_structured_output:
        # Method 1: with_structured_output (preferred for Ollama/OpenAI)
        prompt_template_text = get_phi_identification_prompt(
            language=language or "en",
            structured=True
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", prompt_template_text)
        ])

        # Use LangChain's with_structured_output
        # method="json_schema" uses Ollama's native structured output API (most reliable)
        # method="function_calling" uses tool calling (can hang on some models)
        # method="json_mode" requires format instructions in prompt
        chain = prompt | llm.with_structured_output(
            PHIDetectionResponse,
            method="json_schema"  # 使用 Ollama 原生 structured output API
        )

    else:
        # Method 2: PydanticOutputParser (fallback)
        parser = PydanticOutputParser(pydantic_object=PHIDetectionResponse)

        prompt_template_text = get_phi_identification_prompt(
            language=language or "en",
            structured=True
        )

        # Add format instructions to prompt
        # Escape curly braces in format_instructions to avoid template variable errors
        format_instructions = parser.get_format_instructions()
        format_instructions_escaped = format_instructions.replace("{", "{{").replace("}", "}}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", prompt_template_text + "\n\n" + format_instructions_escaped)
        ])

        # Use LangChain's PydanticOutputParser
        chain = prompt | llm | parser

    logger.debug(f"Built PHI identification chain (structured_output={use_structured_output}, language={language})")
    return chain


def identify_phi(
    text: str,
    context: str,
    llm,
    language: str | None = None,
    tool_results: list[ToolResult] | None = None,
    use_structured_output: bool = True,
) -> tuple[list[PHIEntity], list[PHIIdentificationResult]]:
    """
    Identify PHI using LangChain chain
    使用 LangChain chain 識別 PHI
    
    Primary function for PHI identification. Uses LangChain tools only.
    主要 PHI 識別函數。只使用 LangChain 工具。
    
    Args:
        text: Medical text to analyze
        context: Regulation context
        llm: Language model
        language: Language code (optional)
        tool_results: Pre-scanning tool results (Phase 1 enhancement)
        use_structured_output: Use with_structured_output (True) or PydanticOutputParser (False)
        
    Returns:
        Tuple of (PHIEntity list, PHIIdentificationResult list)
        
    Raises:
        Exception: If LangChain chain fails (no manual fallback)
    """
    # Add tool hints to context if available
    if tool_results:
        tool_hints = format_tool_hints(tool_results)
        context = f"{context}\n\n{tool_hints}"
        logger.debug(f"Added {len(tool_results)} tool hints to context")

    # Build and invoke chain
    chain = build_phi_identification_chain(
        llm=llm,
        language=language,
        use_structured_output=use_structured_output
    )

    # Invoke chain - LangChain handles parsing
    # If it fails, let it raise (no manual JSON parsing!)
    detection_response: PHIDetectionResponse = chain.invoke({
        "context": context,
        "text": text
    })

    # Convert to domain entities
    entities = [result.to_phi_entity() for result in detection_response.entities]

    logger.debug(f"PHI identification complete: {len(entities)} entities found")
    return entities, detection_response.entities


# Backward compatibility aliases
def identify_phi_structured(
    text: str,
    context: str,
    llm,
    language: str | None = None,
    tool_results: list[ToolResult] | None = None
) -> tuple[list[PHIEntity], list[PHIIdentificationResult]]:
    """Backward compatible alias for identify_phi with structured output"""
    return identify_phi(
        text=text,
        context=context,
        llm=llm,
        language=language,
        tool_results=tool_results,
        use_structured_output=True
    )


def identify_phi_with_parser(
    text: str,
    context: str,
    llm,
    language: str | None = None,
    tool_results: list[ToolResult] | None = None
) -> tuple[list[PHIEntity], list[PHIIdentificationResult]]:
    """Use PydanticOutputParser instead of with_structured_output"""
    return identify_phi(
        text=text,
        context=context,
        llm=llm,
        language=language,
        tool_results=tool_results,
        use_structured_output=False
    )


def identify_phi_direct(
    text: str,
    language: str | None,
    regulation_chain,
    llm,
    config,
    get_minimal_context_func,
    return_source: bool = False,
    return_entities: bool = True,
    tool_results: list[ToolResult] | None = None
) -> dict[str, Any]:
    """
    Direct PHI identification for short texts using LangChain
    使用 LangChain 進行短文本的直接 PHI 識別
    
    This orchestrates the full workflow:
    1. Retrieve regulation context (optional)
    2. Build and invoke PHI identification chain
    3. Package results
    
    Args:
        text: Medical text to analyze
        language: Language code
        regulation_chain: Regulation retrieval chain (optional)
        llm: Language model
        config: PHI identification config
        get_minimal_context_func: Function to get minimal context
        return_source: Whether to return source documents
        return_entities: Whether to return entities
        tool_results: Pre-computed tool results (Phase 1 enhancement)
        
    Returns:
        Dict with identification results
    """
    # Step 1: Retrieve regulation context
    regulation_docs = []
    context = ""

    if config.retrieve_regulation_context and regulation_chain:
        # Use first 500 chars for context query
        query_context = text[:500]
        if language:
            query_context = f"[Language: {language}]\n\n{query_context}"

        regulation_docs = regulation_chain.retrieve_by_context(
            medical_context=query_context,
            k=config.regulation_context_k
        )

        # Build context string
        context = "\n\n".join([
            f"[{doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc in regulation_docs
        ])
    else:
        # Use minimal context to reduce prompt length
        context = get_minimal_context_func()

    # Step 2: Identify PHI using LangChain chain
    entities, raw_results = identify_phi(
        text=text,
        context=context,
        llm=llm,
        language=language,
        tool_results=tool_results,
        use_structured_output=config.use_structured_output
    )

    # Step 3: Build response
    response = {
        "text": text,
        "language": language,
        "total_entities": len(entities),
        "has_phi": len(entities) > 0,
    }

    if return_entities:
        response["entities"] = entities
        response["raw_results"] = [r.model_dump() for r in raw_results]

    if return_source:
        response["source_documents"] = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in regulation_docs
        ]

    logger.success(f"PHI identification complete: {len(entities)} entities found")
    return response


# =============================================================================
# DSPy Integration Point (Future)
# =============================================================================
# TODO: Add DSPy-based PHI identification when DSPy optimizer is ready
#
# def identify_phi_dspy(
#     text: str,
#     context: str,
#     dspy_module,
#     language: Optional[str] = None,
# ) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
#     """
#     Identify PHI using DSPy optimized module
#     使用 DSPy 優化模組識別 PHI
#     """
#     pass
