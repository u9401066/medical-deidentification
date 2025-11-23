"""
MapReduce Pattern for PHI Identification
PHI 識別的 MapReduce 模式

Implements MapReduce pattern for processing long medical texts:
- Map stage: Extract PHI from each text chunk
- Reduce stage: Merge and deduplicate results
"""

from typing import List, Tuple, Optional
from dataclasses import replace
from loguru import logger

from langchain_core.prompts import ChatPromptTemplate

from ....domain import PHIEntity
from ....domain.phi_identification_models import (
    PHIIdentificationResult,
    PHIDetectionResponse,
)
from .utils import deduplicate_entities


def build_map_chain(llm):
    """
    Build Map chain for MapReduce pattern
    為 MapReduce 模式構建 Map chain
    
    Map stage: Extract PHI entities from single chunk (NOT full text)
    Map 階段：從單個 chunk 提取 PHI 實體（不包含完整文本）
    
    Args:
        llm: Language model with structured output support
        
    Returns:
        LangChain chain that outputs PHIDetectionResponse
    """
    # Create minimal prompt for map stage
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a PHI identification expert. 
Extract ONLY PHI entities from the medical text, not the full text.

Identify these PHI types:
- Names (patients, doctors, family members)
- Dates (birth, admission, discharge, death)
- Locations (addresses, cities, hospital names)
- Contact info (phone, email, fax)
- IDs (SSN, medical record number, account numbers)
- Ages over 89 years"""),
        ("user", """Identify all PHI in this medical text section:

{page_content}

Return ONLY the PHI entities found.""")
    ])
    
    # Map chain: prompt → LLM with structured output
    return (
        map_prompt 
        | llm.with_structured_output(PHIDetectionResponse)
    )


def merge_phi_results(
    chunk_results: List[Tuple[PHIDetectionResponse, int, str]],
    original_text: str
) -> List[PHIEntity]:
    """
    Merge PHI results from all chunks (Reduce stage)
    合併所有 chunk 的 PHI 結果（Reduce 階段）
    
    This is pure data processing - NO LLM calls needed
    這是純數據處理 - 不需要 LLM 調用
    
    Args:
        chunk_results: List of (detection_response, chunk_start_pos, chunk_text)
        original_text: Original full text
        
    Returns:
        List of PHI entities with adjusted positions
    """
    all_entities = []
    
    for detection_response, chunk_start_pos, chunk_text in chunk_results:
        if not detection_response.entities:
            continue
            
        for result in detection_response.entities:
            # Convert PHIIdentificationResult to PHIEntity
            entity = result.to_phi_entity()
            
            # Find absolute position in original text
            # Use chunk_text.find() to locate entity within chunk first
            entity_text = result.entity_text
            entity_start_in_chunk = chunk_text.find(entity_text, 0)
            
            if entity_start_in_chunk != -1:
                # Calculate absolute position
                absolute_start = chunk_start_pos + entity_start_in_chunk
                absolute_end = absolute_start + len(entity_text)
                
                # Verify entity exists at calculated position
                if (absolute_start < len(original_text) and 
                    original_text[absolute_start:absolute_end] == entity_text):
                    # Create adjusted entity
                    adjusted_entity = replace(
                        entity,
                        start_pos=absolute_start,
                        end_pos=absolute_end
                    )
                    all_entities.append(adjusted_entity)
                else:
                    # Fallback: search in original text
                    absolute_start = original_text.find(entity_text, chunk_start_pos)
                    if absolute_start != -1:
                        adjusted_entity = replace(
                            entity,
                            start_pos=absolute_start,
                            end_pos=absolute_start + len(entity_text)
                        )
                        all_entities.append(adjusted_entity)
                    else:
                        logger.warning(
                            f"Could not find entity '{entity_text[:30]}...' "
                            f"in original text at chunk position {chunk_start_pos}"
                        )
            else:
                logger.warning(f"Could not find entity '{entity_text[:30]}...' in chunk")
    
    # Deduplicate entities (same text at same position)
    unique_entities = deduplicate_entities(all_entities)
    
    logger.debug(
        f"Merged {len(all_entities)} entities → {len(unique_entities)} unique entities"
    )
    
    return unique_entities


def identify_phi_with_map_reduce(
    text: str,
    llm,
    medical_retriever,
    language: Optional[str] = None
) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
    """
    Process long text using MapReduce pattern
    使用 MapReduce 模式處理長文本
    
    Flow:
    1. Split text into chunks
    2. Map: Process each chunk → PHI entities (parallel-ready)
    3. Reduce: Merge all PHI lists, deduplicate, adjust positions
    4. Convert back to raw results
    
    Args:
        text: Medical text to process
        llm: Language model
        medical_retriever: Text retriever for chunking
        language: Language code (optional)
        
    Returns:
        (entities, raw_results) tuple
    """
    logger.info(f"MapReduce: Processing {len(text)} chars")
    
    # 1. Split text into chunks
    chunks = medical_retriever._split_text(text)
    logger.info(f"MapReduce: Split into {len(chunks)} chunks")
    
    # 2. Build map chain
    map_chain = build_map_chain(llm)
    
    # 3. Map stage: Process each chunk
    chunk_results = []
    current_pos = 0
    
    for i, chunk in enumerate(chunks):
        logger.debug(
            f"MapReduce Map {i+1}/{len(chunks)}: "
            f"Processing chunk at pos {current_pos} ({len(chunk)} chars)"
        )
        
        try:
            # Invoke map chain with chunk content
            detection_response = map_chain.invoke({"page_content": chunk})
            
            # Store result with position info
            chunk_results.append((detection_response, current_pos, chunk))
            
            logger.debug(
                f"MapReduce Map {i+1}/{len(chunks)}: "
                f"Found {len(detection_response.entities)} PHI entities"
            )
            
        except Exception as e:
            logger.error(
                f"MapReduce Map {i+1}/{len(chunks)} failed: {e}"
            )
            # Continue with empty result
            empty_response = PHIDetectionResponse(
                entities=[],
                has_phi=False
            )
            chunk_results.append((empty_response, current_pos, chunk))
        
        # Update position for next chunk
        current_pos += len(chunk)
    
    # 4. Reduce stage: Merge results
    logger.debug(f"MapReduce Reduce: Merging {len(chunk_results)} chunk results")
    entities = merge_phi_results(chunk_results, text)
    
    # 5. Convert back to raw results (for backward compatibility)
    raw_results = []
    for entity in entities:
        # Convert PHIEntity back to PHIIdentificationResult
        raw_result = PHIIdentificationResult(
            entity_text=entity.text,
            phi_type=entity.type,
            custom_type_name=entity.custom_type.name if entity.custom_type else None,
            custom_type_description=entity.custom_type.description if entity.custom_type else None,
            start_position=entity.start_pos,
            end_position=entity.end_pos,
            confidence=entity.confidence,
            reason=entity.reason,
            regulation_source=entity.regulation_source,
            masking_action=None,
            is_custom_from_regulation=False,
        )
        raw_results.append(raw_result)
    
    logger.success(
        f"MapReduce complete: {len(entities)} unique PHI entities "
        f"from {len(chunks)} chunks"
    )
    
    return entities, raw_results
