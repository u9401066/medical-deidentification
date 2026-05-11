"""
MapReduce Pattern for PHI Identification
PHI 識別的 MapReduce 模式

Implements MapReduce pattern using LangChain for processing long medical texts:
- Map stage: Extract PHI from each text chunk using chain
- Reduce stage: Merge and deduplicate results (pure data processing)
"""

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from loguru import logger

from ....domain import PHIEntity
from ....domain.phi_identification_models import (
    PHIDetectionResponse,
)
from ...llm.factory import get_structured_output_method
from ...prompts import get_phi_map_reduce_prompt, get_system_message
from .utils import deduplicate_entities

ProgressCallback = Callable[[dict[str, Any]], None]


def _emit_progress(
    progress_callback: ProgressCallback | None,
    event: str,
    **payload: Any,
) -> None:
    """Emit chunk-level progress without allowing observers to fail processing."""
    if progress_callback is None:
        return

    try:
        progress_callback({"event": event, **payload})
    except Exception as exc:
        logger.warning(f"Progress callback failed for {event}: {exc}")


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
    # Auto-detect best method based on provider:
    # - Ollama: json_schema (native)
    # - OpenAI: json_schema
    # - Anthropic: function_calling
    method = get_structured_output_method(llm)
    
    if method:
        map_chain: Runnable = (
            map_prompt
            | llm.with_structured_output(PHIDetectionResponse, method=method)
        )
    else:
        map_chain: Runnable = (
            map_prompt
            | llm.with_structured_output(PHIDetectionResponse)
        )

    logger.debug(f"Built MapReduce map chain (method={method})")
    return map_chain


def merge_phi_results(
    chunk_results: list[tuple[PHIDetectionResponse, int, str]],
    original_text: str
) -> list[PHIEntity]:
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
                            "Could not align entity in original text "
                            f"at chunk position {chunk_start_pos}, entity_len={len(entity_text)}"
                        )
            else:
                logger.warning(f"Could not align entity in chunk, entity_len={len(entity_text)}")

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
    language: str | None = None,
    progress_callback: ProgressCallback | None = None,
) -> list[PHIEntity]:
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
        progress_callback: Optional progress event callback
        
    Returns:
        List of PHIEntity with absolute positions
    """
    logger.info(f"MapReduce: Processing {len(text)} chars with LangChain")

    # 1. Split text into chunks
    chunks = text_splitter.split_text(text)
    total_chunks = len(chunks)
    logger.info(f"MapReduce: Split into {total_chunks} chunks")
    _emit_progress(
        progress_callback,
        "chunks_prepared",
        text_length=len(text),
        total_chunks=total_chunks,
        language=language,
    )

    if total_chunks == 0:
        _emit_progress(
            progress_callback,
            "reduce_completed",
            total_chunks=0,
            total_phi_found=0,
            unique_entities=0,
        )
        return []

    # 2. Build map chain (LangChain Runnable)
    map_chain = build_map_chain(llm)

    # 3. Map stage: Process each chunk using the chain
    chunk_results = []
    current_pos = 0

    for i, chunk in enumerate(chunks):
        import time
        chunk_start = time.time()

        progress_pct = (i / total_chunks) * 100
        logger.info(
            f"MapReduce Map {i+1}/{total_chunks} ({progress_pct:.1f}%): "
            f"Processing chunk at pos {current_pos} ({len(chunk)} chars)"
        )
        _emit_progress(
            progress_callback,
            "chunk_started",
            chunk_index=i,
            chunk_number=i + 1,
            total_chunks=total_chunks,
            chunk_start_pos=current_pos,
            chunk_end_pos=current_pos + len(chunk),
            chunk_size=len(chunk),
        )

        try:
            # Invoke LangChain Runnable with chunk content
            # The chain will apply prompt template and call LLM
            detection_response = map_chain.invoke({"page_content": chunk})

            # Calculate performance metrics
            chunk_duration = time.time() - chunk_start
            tokens_per_sec = len(chunk.split()) / chunk_duration if chunk_duration > 0 else 0

            # Store result with position info
            chunk_results.append((detection_response, current_pos, chunk))

            logger.info(
                f"MapReduce Map {i+1}/{total_chunks}: "
                f"Found {len(detection_response.entities)} PHI entities "
                f"({chunk_duration:.2f}s, {tokens_per_sec:.1f} tokens/sec)"
            )
            _emit_progress(
                progress_callback,
                "chunk_completed",
                chunk_index=i,
                chunk_number=i + 1,
                total_chunks=total_chunks,
                chunk_start_pos=current_pos,
                chunk_end_pos=current_pos + len(chunk),
                chunk_size=len(chunk),
                duration_seconds=chunk_duration,
                entities_found=len(detection_response.entities),
                success=True,
            )

        except Exception as e:
            logger.error(
                f"MapReduce Map {i+1}/{total_chunks} failed: {e}"
            )
            # Continue with empty result
            empty_response = PHIDetectionResponse(
                entities=[],
                has_phi=False
            )
            chunk_results.append((empty_response, current_pos, chunk))
            _emit_progress(
                progress_callback,
                "chunk_completed",
                chunk_index=i,
                chunk_number=i + 1,
                total_chunks=total_chunks,
                chunk_start_pos=current_pos,
                chunk_end_pos=current_pos + len(chunk),
                chunk_size=len(chunk),
                duration_seconds=time.time() - chunk_start,
                entities_found=0,
                success=False,
                error_message=str(e),
            )

        # Update position for next chunk
        current_pos += len(chunk)

    # 4. Reduce stage: Merge results (pure data processing, no LLM)
    logger.info(f"MapReduce Reduce: Merging {len(chunk_results)} chunk results...")
    _emit_progress(
        progress_callback,
        "reduce_started",
        total_chunks=total_chunks,
        processed_chunks=len(chunk_results),
    )

    # Calculate overall statistics
    successful_chunks = len([r for r in chunk_results if r[0].entities])
    total_phi_found = sum(len(r[0].entities) for r in chunk_results)

    entities = merge_phi_results(chunk_results, text)
    _emit_progress(
        progress_callback,
        "reduce_completed",
        total_chunks=total_chunks,
        processed_chunks=len(chunk_results),
        successful_chunks=successful_chunks,
        total_phi_found=total_phi_found,
        unique_entities=len(entities),
    )

    logger.success(
        f"MapReduce complete: {len(entities)} unique PHI entities identified "
        f"({total_phi_found} raw detections from {successful_chunks}/{total_chunks} chunks)"
    )

    return entities
