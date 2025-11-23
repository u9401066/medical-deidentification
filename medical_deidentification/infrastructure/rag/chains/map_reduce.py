"""
MapReduce Pattern for PHI Identification
PHI 識別的 MapReduce 模式

Implements MapReduce pattern using LangChain for processing long medical texts:
- Map stage: Extract PHI from each text chunk using chain
- Reduce stage: Merge and deduplicate results (pure data processing)
"""

from typing import List, Tuple, Optional
from dataclasses import replace
from loguru import logger

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from ....domain import PHIEntity
from ....domain.phi_identification_models import (
    PHIIdentificationResult,
    PHIDetectionResponse,
)
from ...prompts import get_phi_map_reduce_prompt, get_system_message
from .utils import deduplicate_entities


def build_map_chain(llm) -> Runnable:
    """
    Build Map chain for MapReduce pattern using centralized prompts
    使用集中化 prompts 為 MapReduce 模式構建 Map chain
    
    This is a LangChain Runnable that:
    1. Takes chunk text as input
    2. Applies prompt template
    3. Invokes LLM with structured output
    4. Returns PHIDetectionResponse
    
    Map stage: Extract PHI entities from single chunk (NOT full text)
    Map 階段：從單個 chunk 提取 PHI 實體（不包含完整文本）
    
    Args:
        llm: Language model with structured output support
        
    Returns:
        LangChain Runnable that outputs PHIDetectionResponse
    """
    # Get prompt template from centralized prompts module
    prompt_text = get_phi_map_reduce_prompt()
    system_message = get_system_message("phi_expert")
    
    # Create ChatPromptTemplate using LangChain
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", prompt_text)
    ])
    
    # Build chain: prompt → LLM with structured output
    # This creates a Runnable that can be invoked with {"page_content": "..."}
    map_chain: Runnable = (
        map_prompt 
        | llm.with_structured_output(PHIDetectionResponse)
    )
    
    logger.debug("Built MapReduce map chain with centralized prompt and LangChain Runnable")
    return map_chain


def merge_phi_results(
    chunk_results: List[Tuple[PHIDetectionResponse, int, str]],
    original_text: str
) -> List[PHIEntity]:
    """
    Merge PHI results from all chunks (Reduce stage)
    合併所有 chunk 的 PHI 結果（Reduce 階段）
    
    This is pure data processing - NO LLM calls needed
    這是純數據處理 - 不需要 LLM 調用
    
    Process:
    1. Iterate through all chunk results
    2. Convert PHIIdentificationResult to PHIEntity
    3. Adjust positions from chunk-relative to absolute
    4. Deduplicate overlapping entities
    
    Args:
        chunk_results: List of (detection_response, chunk_start_pos, chunk_text)
        original_text: Original full text for position verification
        
    Returns:
        List of PHIEntity with absolute positions
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
                    # Create adjusted entity with absolute positions
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
    
    # Deduplicate entities (same text at overlapping positions)
    unique_entities = deduplicate_entities(all_entities)
    
    logger.debug(
        f"Merged {len(all_entities)} entities → {len(unique_entities)} unique entities"
    )
    
    return unique_entities


def identify_phi_with_map_reduce(
    text: str,
    llm,
    text_splitter,
    language: Optional[str] = None
) -> List[PHIEntity]:
    """
    Process long text using MapReduce pattern with LangChain
    使用 LangChain 的 MapReduce 模式處理長文本
    
    Flow:
    1. Split text into chunks (via text_splitter)
    2. Map: Build chain and process each chunk → PHI entities (parallel-ready)
    3. Reduce: Merge all PHI lists, deduplicate, adjust positions
    
    Args:
        text: Medical text to process
        llm: Language model
        text_splitter: MedicalTextSplitter for chunking
        language: Language code (optional, for future multilingual support)
        
    Returns:
        List of PHIEntity with absolute positions
    """
    logger.info(f"MapReduce: Processing {len(text)} chars with LangChain")
    
    # 1. Split text into chunks
    chunks = text_splitter.split_text(text)
    logger.info(f"MapReduce: Split into {len(chunks)} chunks")
    
    # 2. Build map chain (LangChain Runnable)
    map_chain = build_map_chain(llm)
    
    # 3. Map stage: Process each chunk using the chain
    chunk_results = []
    current_pos = 0
    
    for i, chunk in enumerate(chunks):
        logger.debug(
            f"MapReduce Map {i+1}/{len(chunks)}: "
            f"Processing chunk at pos {current_pos} ({len(chunk)} chars)"
        )
        
        try:
            # Invoke LangChain Runnable with chunk content
            # The chain will apply prompt template and call LLM
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
    
    # 4. Reduce stage: Merge results (pure data processing, no LLM)
    logger.debug(f"MapReduce Reduce: Merging {len(chunk_results)} chunk results")
    entities = merge_phi_results(chunk_results, text)
    
    logger.success(f"MapReduce complete: {len(entities)} PHI entities identified")
    
    return entities
