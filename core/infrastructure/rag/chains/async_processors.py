"""
Async PHI Identification Processors - Python 3.12 Optimized
異步 PHI 識別處理器 - Python 3.12 優化版

利用 Python 3.12 的效能改進:
1. asyncio 改進 - 更快的事件循環
2. 內聯 comprehension (PEP 709) - 自動優化
3. 更快的 f-string 處理
4. TaskGroup (Python 3.11+) - 結構化並發

Requires: Python 3.12+
"""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from loguru import logger

from ....domain.phi_identification_models import PHIDetectionResponse
from ...llm.factory import get_structured_output_method
from ...prompts import get_phi_identification_prompt, get_system_message


@dataclass(slots=True, frozen=True)  # Python 3.10+ slots for memory efficiency
class ChunkResult:
    """Result from processing a single chunk"""
    chunk_index: int
    response: PHIDetectionResponse | None
    error: str | None = None


async def process_chunk_async(
    chain: Runnable,
    chunk: str,
    chunk_index: int,
    context: str = ""
) -> ChunkResult:
    """
    Process a single chunk asynchronously
    異步處理單個文本塊
    
    Args:
        chain: LangChain runnable chain
        chunk: Text chunk to process
        chunk_index: Index of this chunk
        context: Optional context for RAG
        
    Returns:
        ChunkResult with response or error
    """
    try:
        # Use ainvoke for async invocation
        result = await chain.ainvoke({"context": context, "text": chunk})
        return ChunkResult(chunk_index=chunk_index, response=result)
    except Exception as e:
        logger.warning(f"Chunk {chunk_index} failed: {e}")
        return ChunkResult(chunk_index=chunk_index, response=None, error=str(e))


async def process_chunks_parallel(
    chain: Runnable,
    chunks: Sequence[str],
    context: str = "",
    max_concurrency: int = 3
) -> list[ChunkResult]:
    """
    Process multiple chunks in parallel using Python 3.11+ TaskGroup
    使用 Python 3.11+ TaskGroup 並行處理多個文本塊
    
    Args:
        chain: LangChain runnable chain
        chunks: List of text chunks
        context: Optional context for RAG
        max_concurrency: Maximum concurrent tasks (default: 3)
        
    Returns:
        List of ChunkResults in original order
    """
    # Use semaphore to limit concurrency (avoid overloading Ollama)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_semaphore(chunk: str, index: int) -> ChunkResult:
        async with semaphore:
            return await process_chunk_async(chain, chunk, index, context)

    # Python 3.11+ TaskGroup for structured concurrency
    results: list[ChunkResult] = []

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(process_with_semaphore(chunk, i))
            for i, chunk in enumerate(chunks)
        ]

    # Collect results (tasks are done after TaskGroup exits)
    results = [task.result() for task in tasks]

    # Sort by chunk_index to maintain order
    results.sort(key=lambda r: r.chunk_index)

    return results


def merge_chunk_results(results: list[ChunkResult]) -> PHIDetectionResponse:
    """
    Merge multiple chunk results into a single response
    合併多個塊結果為單一回應
    
    Args:
        results: List of ChunkResults
        
    Returns:
        Merged PHIDetectionResponse
    """
    all_entities = []

    for result in results:
        if result.response and result.response.entities:
            all_entities.extend(result.response.entities)

    return PHIDetectionResponse(
        entities=all_entities,
        total_entities=len(all_entities),
        has_phi=len(all_entities) > 0
    )


def build_async_phi_chain(
    llm,
    language: str | None = None
) -> Runnable:
    """
    Build async-capable PHI identification chain
    建立支援異步的 PHI 識別 chain
    
    Uses json_schema method for reliable structured output
    使用 json_schema 方法以獲得可靠的結構化輸出
    
    Args:
        llm: Language model (ChatOllama or compatible)
        language: Language code (optional)
        
    Returns:
        LangChain Runnable that supports ainvoke
    """
    system_message = get_system_message()
    prompt_template_text = get_phi_identification_prompt(
        language=language or "en",
        structured=True
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", prompt_template_text)
    ])

    # Auto-detect best method based on provider:
    # - Ollama: json_schema (native, most reliable)
    # - OpenAI: json_schema
    # - Anthropic: function_calling (only supported method)
    method = get_structured_output_method(llm)
    
    if method:
        chain = prompt | llm.with_structured_output(
            PHIDetectionResponse,
            method=method
        )
    else:
        chain = prompt | llm.with_structured_output(PHIDetectionResponse)

    logger.debug(f"Built async PHI chain (language={language}, method={method})")
    return chain


async def identify_phi_async(
    llm,
    text: str,
    language: str | None = None,
    chunk_size: int = 2000,
    max_concurrency: int = 3,
    context: str = ""
) -> PHIDetectionResponse:
    """
    High-level async PHI identification with automatic chunking
    高階異步 PHI 識別，自動分塊處理
    
    Example:
        ```python
        import asyncio
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(model="granite4:1b")
        result = asyncio.run(identify_phi_async(llm, long_text))
        ```
    
    Args:
        llm: Language model
        text: Text to analyze (can be long)
        language: Language code
        chunk_size: Maximum characters per chunk
        max_concurrency: Maximum parallel requests
        context: Optional RAG context
        
    Returns:
        Merged PHIDetectionResponse from all chunks
    """
    # Build chain
    chain = build_async_phi_chain(llm, language)

    # Split into chunks if needed
    if len(text) <= chunk_size:
        chunks = [text]
    else:
        # Simple chunking by character count (could be improved)
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        logger.info(f"Split text into {len(chunks)} chunks")

    # Process chunks in parallel
    if len(chunks) == 1:
        result = await process_chunk_async(chain, chunks[0], 0, context)
        return result.response or PHIDetectionResponse(entities=[], total_entities=0, has_phi=False)
    else:
        results = await process_chunks_parallel(
            chain, chunks, context, max_concurrency
        )
        return merge_chunk_results(results)


# Convenience function for sync code
def identify_phi_sync(
    llm,
    text: str,
    language: str | None = None,
    chunk_size: int = 2000,
    max_concurrency: int = 3,
    context: str = ""
) -> PHIDetectionResponse:
    """
    Sync wrapper for identify_phi_async
    identify_phi_async 的同步包裝
    
    For use in non-async code:
        ```python
        result = identify_phi_sync(llm, text)
        ```
    """
    return asyncio.run(
        identify_phi_async(llm, text, language, chunk_size, max_concurrency, context)
    )
