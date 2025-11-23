"""
PHI Identification Processors
PHI 識別處理器

Core processors for PHI identification:
- Direct processing (short texts)
- Structured output processing (Ollama native)
- JSON fallback processing
"""

from typing import List, Tuple, Dict, Any, Optional
import json
import re
from loguru import logger

from ....domain import PHIEntity
from ....domain.phi_identification_models import (
    PHIIdentificationResult,
    PHIDetectionResponse,
)
from ...prompts import get_phi_identification_prompt


def identify_phi_structured(
    text: str,
    context: str,
    llm,
    language: Optional[str] = None
) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
    """
    Identify PHI using structured output (Ollama native or LangChain)
    使用結構化輸出識別 PHI（Ollama 原生或 LangChain）
    
    Args:
        text: Medical text to analyze
        context: Regulation context
        llm: Language model
        language: Language code (optional)
        
    Returns:
        Tuple of (PHIEntity list, PHIIdentificationResult list)
    """
    # Get prompt template
    prompt_template = get_phi_identification_prompt(
        language=language or "en",
        structured=True
    )
    prompt = prompt_template.format(context=context, text=text)
    
    try:
        # Check if using Ollama (check model name or endpoint)
        if hasattr(llm, 'model') and 'llama' in str(llm.model).lower():
            try:
                import ollama
                
                # Extract model name from LLM config
                model_name = llm.model if hasattr(llm, 'model') else 'llama3.1:8b'
                
                logger.debug(f"Using Ollama native structured output with model: {model_name}")
                
                # Use Ollama native structured output with timeout
                client = ollama.Client(host='http://localhost:11434', timeout=120.0)
                response = client.chat(
                    model=model_name,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    format=PHIDetectionResponse.model_json_schema(),
                )
                
                # Parse response
                detection_response = PHIDetectionResponse.model_validate_json(
                    response['message']['content']
                )
                
                # Convert to domain entities
                entities = [result.to_phi_entity() for result in detection_response.entities]
                
                logger.debug(f"Ollama structured output successful: {len(entities)} entities")
                return entities, detection_response.entities
                
            except ImportError:
                logger.warning("ollama package not available, falling back to LangChain wrapper")
            except Exception as e:
                logger.warning(f"Ollama native structured output failed: {e}, falling back to LangChain")
        
        # Fallback to LangChain with_structured_output
        logger.debug("Using LangChain with_structured_output")
        llm_structured = llm.with_structured_output(PHIDetectionResponse)
        detection_response: PHIDetectionResponse = llm_structured.invoke(prompt)
        
        # Convert to domain entities
        entities = [result.to_phi_entity() for result in detection_response.entities]
        
        return entities, detection_response.entities
        
    except Exception as e:
        logger.error(f"Structured output failed: {e}, falling back to JSON parsing")
        return identify_phi_json_fallback(text, context, llm, language)


def identify_phi_json_fallback(
    text: str,
    context: str,
    llm,
    language: Optional[str] = None
) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
    """
    Fallback method using JSON parsing
    降級方法使用 JSON 解析
    
    Args:
        text: Medical text to analyze
        context: Regulation context
        llm: Language model
        language: Language code (optional)
        
    Returns:
        Tuple of (PHIEntity list, PHIIdentificationResult list)
    """
    prompt_template = get_phi_identification_prompt(language=language or "en")
    prompt = prompt_template.format(context=context, question=text)
    
    response_text = ""  # Initialize for error logging
    try:
        # Use invoke() for compatibility with all LangChain chat models
        response = llm.invoke(prompt)
        # Get content from response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean markdown code blocks (```json ... ``` or ``` ... ```)
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text.strip())
        response_text = re.sub(r'\s*```$', '', response_text.strip())
        
        # Try to extract JSON from response text if it contains extra text
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            json_str = json_match.group(0)
            logger.debug(f"Extracted JSON from response: {json_str[:200]}...")
        else:
            json_str = response_text
            logger.debug(f"Using full response as JSON: {response_text[:200]}...")
        
        json_data = json.loads(json_str)
        
        raw_results = [PHIIdentificationResult(**item) for item in json_data]
        entities = [result.to_phi_entity() for result in raw_results]
        
        return entities, raw_results
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Response text (first 500 chars): {response_text[:500]}")
        return [], []


def identify_phi_direct(
    text: str,
    language: Optional[str],
    regulation_chain,
    llm,
    config,
    get_minimal_context_func,
    return_source: bool = False,
    return_entities: bool = True
) -> Dict[str, Any]:
    """
    Direct PHI identification for short texts
    短文本的直接 PHI 識別
    
    Args:
        text: Medical text to analyze
        language: Language code
        regulation_chain: Regulation retrieval chain (optional)
        llm: Language model
        config: PHI identification config
        get_minimal_context_func: Function to get minimal context
        return_source: Whether to return source documents
        return_entities: Whether to return entities
        
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
    
    # Step 2: Identify PHI using LLM
    if config.use_structured_output:
        entities, raw_results = identify_phi_structured(
            text=text,
            context=context,
            llm=llm,
            language=language
        )
    else:
        entities, raw_results = identify_phi_json_fallback(
            text=text,
            context=context,
            llm=llm,
            language=language
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
