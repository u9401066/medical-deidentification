"""
PHI Identification Chain Utilities
PHI 識別鏈工具函數

Utility functions for PHI identification chain:
- Context management
- Entity deduplication
- Entity validation
"""

from typing import List, Dict, Any, Optional
import json
from loguru import logger

from ....domain import PHIEntity
from ...prompts import DEFAULT_HIPAA_SAFE_HARBOR_RULES, get_phi_validation_prompt


def get_minimal_context(retrieve_regulation_context: bool = False) -> str:
    """
    Get minimal context to reduce prompt length
    獲取最小化上下文以減少 prompt 長度
    
    Args:
        retrieve_regulation_context: Whether RAG is enabled
        
    Returns:
        Minimal context string (~300 chars instead of 800+)
    """
    if retrieve_regulation_context:
        # If RAG enabled, could minimize RAG-retrieved context in future
        # For now, return default rules
        return DEFAULT_HIPAA_SAFE_HARBOR_RULES
    else:
        # Use minimal context (from 800 chars → ~300 chars)
        # Keep essential PHI types, remove verbose explanations
        return """Identify PHI according to HIPAA Safe Harbor:
- Names (patients, relatives, employers)
- All dates (birth, admission, discharge, death, ages >89)
- Geographic locations smaller than state (cities, addresses, ZIP codes)
- Phone numbers, fax numbers, email addresses
- SSNs, medical record numbers, health plan numbers, account numbers
- Certificate/license numbers, vehicle/device identifiers/serial numbers
- URLs, IP addresses
- Biometric identifiers, full-face photos
- Any other unique identifying numbers/codes"""


def deduplicate_entities(entities: List[PHIEntity]) -> List[PHIEntity]:
    """
    Remove duplicate entities based on text and position overlap
    根據文本和位置重疊移除重複實體
    
    Args:
        entities: List of PHI entities (possibly with duplicates)
        
    Returns:
        List of unique PHI entities
    """
    if not entities:
        return []
    
    # Sort by start position
    sorted_entities = sorted(entities, key=lambda e: e.start_pos)
    
    unique = []
    for entity in sorted_entities:
        # Check if this entity overlaps with any existing unique entity
        is_duplicate = False
        for existing in unique:
            # Check for overlap
            if (entity.start_pos < existing.end_pos and 
                entity.end_pos > existing.start_pos):
                # Overlapping entities
                if entity.text == existing.text:
                    is_duplicate = True
                    break
                # If text similar (>80% overlap), consider duplicate
                overlap_len = min(entity.end_pos, existing.end_pos) - max(entity.start_pos, existing.start_pos)
                min_len = min(len(entity.text), len(existing.text))
                if overlap_len / min_len > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique.append(entity)
    
    return unique


def validate_entity(
    entity_text: str,
    phi_type: str,
    regulation_chain = None,
    llm = None,
    retrieve_evidence: bool = False
) -> Dict[str, Any]:
    """
    Validate if an entity is actually PHI according to regulations
    根據法規驗證實體是否確實為 PHI
    
    Args:
        entity_text: The entity text to validate
        phi_type: The PHI type to validate against
        regulation_chain: RegulationRetrievalChain for retrieving regulations
        llm: LLM for validation
        retrieve_evidence: Whether to retrieve supporting evidence
        
    Returns:
        Validation result with should_mask, confidence, evidence
    """
    result = {
        "entity_text": entity_text,
        "phi_type": phi_type,
        "should_mask": False,
        "confidence": 0.0,
        "evidence": []
    }
    
    if retrieve_evidence and regulation_chain and llm:
        try:
            # Retrieve relevant regulations
            regulation_docs = regulation_chain.get_phi_definitions([phi_type])
            
            result["evidence"] = [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in regulation_docs
            ]
            
            # Use LLM to validate
            validation_prompt_template = get_phi_validation_prompt()
            validation_prompt = validation_prompt_template.format(
                entity_text=entity_text,
                phi_type=phi_type,
                regulations="\n".join([doc.page_content for doc in regulation_docs])
            )
            
            # Use invoke() for compatibility with all LangChain chat models
            response = llm.invoke(validation_prompt)
            llm_response = response.content if hasattr(response, 'content') else str(response)
            
            # Parse validation result
            validation = json.loads(llm_response)
            result["should_mask"] = validation.get("should_mask", False)
            result["confidence"] = validation.get("confidence", 0.0)
            result["reason"] = validation.get("reason", "")
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM validation response")
        except Exception as e:
            logger.error(f"Entity validation failed: {e}")
    
    return result
