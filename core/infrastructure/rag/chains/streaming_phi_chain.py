"""
Streaming PHI Chain | 串流 PHI Chain

Streaming PHI detection for unlimited file sizes with:
- FIFO stateless chunk processing
- Checkpoint/resume support
- Tool calling per chunk
- RAG on/off configuration

無限檔案大小的串流 PHI 檢測：
- FIFO 無狀態分塊處理
- 斷點續處理支援
- 每個 chunk 可呼叫工具
- RAG 開關配置

Usage:
    chain = StreamingPHIChain(
        llm=my_llm,
        chunk_size=2000,
        checkpoint_dir="./checkpoints",
        enable_rag=True,
        enable_tools=True,
    )
    
    # Process large file with auto-resume
    for result in chain.process_file("large_medical_record.txt"):
        print(f"Chunk {result.chunk_id}: {len(result.entities)} PHI found")
    
    # Check progress
    progress = chain.get_progress("large_medical_record.txt")
    print(f"Progress: {progress['progress_percent']:.1f}%")
"""

import json
import os
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger

from ....domain import PHIEntity
from ...llm.config import LLMConfig
from .streaming_processor import (
    ChunkInfo,
    ChunkResult,
    StreamingChunkProcessor,
)


@dataclass
class StreamingPHIConfig:
    """Configuration for streaming PHI chain"""
    # Chunking
    chunk_size: int = 2000
    chunk_overlap: int = 100

    # LLM
    llm_config: LLMConfig | None = None
    use_structured_output: bool = True

    # RAG
    enable_rag: bool = True
    rag_k: int = 3

    # Tools
    enable_tools: bool = True
    max_tool_calls_per_chunk: int = 5

    # Checkpoint
    checkpoint_dir: str | None = None
    checkpoint_interval: int = 1

    # Output
    output_dir: str | None = None
    output_format: str = "jsonl"  # jsonl, json, or csv


@dataclass
class PHIChunkResult:
    """Result from processing a single chunk for PHI"""
    chunk_id: int
    start_pos: int
    end_pos: int
    entities: list[PHIEntity]
    raw_text: str
    success: bool
    error: str | None = None
    processing_time_ms: float = 0.0
    tool_calls_made: int = 0
    rag_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "entities": [
                {
                    "text": e.text,
                    "type": e.type.value,
                    "start_pos": e.start_pos,
                    "end_pos": e.end_pos,
                    "confidence": e.confidence,
                }
                for e in self.entities
            ],
            "success": self.success,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms,
            "tool_calls_made": self.tool_calls_made,
            "rag_used": self.rag_used,
        }


class StreamingPHIChain:
    """
    Streaming PHI Detection Chain
    串流 PHI 檢測 Chain
    
    Features:
    - Process unlimited file sizes
    - FIFO stateless (one chunk at a time)
    - Checkpoint/resume for long processing
    - Per-chunk tool calling
    - RAG on/off switch
    
    特點：
    - 處理無限大檔案
    - FIFO 無狀態（一次一個 chunk）
    - 長時間處理的斷點續處理
    - 每個 chunk 可呼叫工具
    - RAG 開關
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        config: StreamingPHIConfig | None = None,
        regulation_chain=None,
        tools: list[BaseTool] | None = None,
    ):
        """
        Initialize streaming PHI chain
        
        Args:
            llm: Language model
            config: Streaming configuration
            regulation_chain: RAG regulation chain (optional)
            tools: PHI detection tools (optional)
        """
        self.config = config or StreamingPHIConfig()
        self.regulation_chain = regulation_chain
        self.tools = tools or []

        # Initialize LLM
        if llm:
            self.llm = llm
        elif self.config.llm_config:
            from ...llm.factory import create_llm
            self.llm = create_llm(self.config.llm_config)
        else:
            self.llm = None

        # Bind tools to LLM if available
        if self.llm and self.config.enable_tools and self.tools:
            try:
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            except (AttributeError, NotImplementedError):
                self.llm_with_tools = self.llm
                logger.warning("LLM does not support tool binding")
        else:
            self.llm_with_tools = self.llm

        # RAG context cache (minimal, for current chunk only)
        self._rag_context: str | None = None

        # Create output directory if specified
        if self.config.output_dir:
            os.makedirs(self.config.output_dir, exist_ok=True)

        # Initialize streaming processor
        self._processor = StreamingChunkProcessor(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            process_func=self._process_chunk,
            output_func=self._output_result,
            checkpoint_dir=self.config.checkpoint_dir,
            checkpoint_interval=self.config.checkpoint_interval,
        )

        logger.info(
            f"StreamingPHIChain initialized: "
            f"chunk_size={self.config.chunk_size}, "
            f"rag={'on' if self.config.enable_rag else 'off'}, "
            f"tools={'on' if self.config.enable_tools else 'off'}"
        )

    def process_file(
        self,
        file_path: str,
        resume: bool = True,
        language: str | None = None,
    ) -> Generator[PHIChunkResult, None, None]:
        """
        Process file with streaming chunks
        串流處理檔案
        
        Args:
            file_path: Path to medical text file
            resume: Whether to resume from checkpoint
            language: Language hint
            
        Yields:
            PHIChunkResult for each processed chunk
        """
        self._current_language = language
        self._current_file = file_path
        self._output_file = None

        # Setup output file if configured
        if self.config.output_dir:
            output_name = os.path.basename(file_path) + ".phi.jsonl"
            self._output_file = open(
                os.path.join(self.config.output_dir, output_name),
                'a', encoding='utf-8'
            )

        try:
            for chunk_result in self._processor.process_file(file_path, resume):
                # Convert to PHIChunkResult
                phi_result = self._convert_result(chunk_result)
                yield phi_result
        finally:
            if self._output_file:
                self._output_file.close()
                self._output_file = None

    def process_text(
        self,
        text: str,
        text_id: str = "text",
        resume: bool = True,
        language: str | None = None,
    ) -> Generator[PHIChunkResult, None, None]:
        """
        Process text string with streaming chunks
        串流處理文本字串
        """
        self._current_language = language
        self._current_file = text_id
        self._output_file = None

        for chunk_result in self._processor.process_text(text, text_id, resume):
            phi_result = self._convert_result(chunk_result)
            yield phi_result

    def _process_chunk(self, content: str, chunk_info: ChunkInfo) -> dict[str, Any]:
        """
        Process a single chunk (stateless)
        處理單個 chunk（無狀態）
        
        This is called by StreamingChunkProcessor for each chunk.
        """
        entities: list[PHIEntity] = []
        tool_calls = 0
        rag_used = False

        # Step 1: Get RAG context (if enabled)
        context = ""
        if self.config.enable_rag and self.regulation_chain:
            try:
                context = self._get_rag_context(content)
                rag_used = True
            except Exception as e:
                logger.warning(f"RAG failed for chunk {chunk_info.chunk_id}: {e}")
                context = self._get_minimal_context()
        else:
            context = self._get_minimal_context()

        # Step 2: Run tools (if enabled)
        tool_hints = ""
        if self.config.enable_tools and self.tools:
            tool_results, tool_calls = self._run_tools(content, chunk_info)
            if tool_results:
                tool_hints = self._format_tool_hints(tool_results)

        # Step 3: LLM identification
        if self.llm:
            try:
                llm_entities = self._identify_with_llm(
                    content, context, tool_hints, chunk_info
                )
                entities.extend(llm_entities)
            except Exception as e:
                logger.error(f"LLM identification failed: {e}")

        return {
            "entities": entities,
            "tool_calls": tool_calls,
            "rag_used": rag_used,
            "raw_text": content,
        }

    def _get_rag_context(self, text: str) -> str:
        """Get regulation context from RAG"""
        if not self.regulation_chain:
            return self._get_minimal_context()

        query = text[:500]  # Use first 500 chars for query
        if self._current_language:
            query = f"[Language: {self._current_language}]\n{query}"

        try:
            docs = self.regulation_chain.retrieve_by_context(
                medical_context=query,
                k=self.config.rag_k
            )

            context_parts = []
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                context_parts.append(f"[{source}]\n{doc.page_content}")

            return "\n\n".join(context_parts) if context_parts else self._get_minimal_context()
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return self._get_minimal_context()

    def _get_minimal_context(self) -> str:
        """Minimal context when RAG is disabled"""
        return """PHI types to identify:
- NAME: Patient names, doctor names
- ID: National IDs, medical record numbers
- DATE: Dates (except year alone)
- PHONE: Phone numbers, fax numbers
- EMAIL: Email addresses
- LOCATION: Addresses, hospital names
- AGE_OVER_89: Ages over 89"""

    def _run_tools(
        self,
        content: str,
        chunk_info: ChunkInfo
    ) -> tuple[list[dict[str, Any]], int]:
        """Run PHI detection tools on chunk"""
        results = []
        calls = 0

        for tool in self.tools[:self.config.max_tool_calls_per_chunk]:
            try:
                result = tool.invoke({"text": content})
                results.append({
                    "tool": tool.name,
                    "result": result,
                })
                calls += 1
            except Exception as e:
                logger.debug(f"Tool {tool.name} failed: {e}")

        return results, calls

    def _format_tool_hints(self, tool_results: list[dict[str, Any]]) -> str:
        """Format tool results as hints for LLM"""
        lines = ["[Tool Detection Hints]"]
        for tr in tool_results:
            lines.append(f"- {tr['tool']}: {tr['result'][:200]}...")
        return "\n".join(lines)

    def _identify_with_llm(
        self,
        content: str,
        context: str,
        tool_hints: str,
        chunk_info: ChunkInfo,
    ) -> list[PHIEntity]:
        """
        Identify PHI using LLM - uses LangChain with_structured_output
        使用 LLM 識別 PHI - 使用 LangChain with_structured_output
        
        Uses LangChain Runnable pattern: prompt | llm.with_structured_output(schema)
        使用 LangChain Runnable 模式: prompt | llm.with_structured_output(schema)
        """
        from .processors import identify_phi

        if not self.llm:
            logger.warning("LLM not available, skipping LLM identification")
            return []

        # Combine context with tool hints
        full_context = context
        if tool_hints:
            full_context = f"{context}\n\n{tool_hints}"

        try:
            logger.info(f"Chunk {chunk_info.chunk_id}: Starting LLM identification (text length: {len(content)})...")
            import time
            start_time = time.time()

            # Use identify_phi from processors.py
            # This uses: prompt | llm.with_structured_output(PHIDetectionResponse)
            entities, _ = identify_phi(
                text=content,
                context=full_context,
                llm=self.llm,
                language=self._current_language,
                tool_results=None,  # Tool hints already in context
                use_structured_output=self.config.use_structured_output,
            )

            elapsed = time.time() - start_time
            logger.info(f"Chunk {chunk_info.chunk_id}: LLM call completed in {elapsed:.2f}s, found {len(entities)} entities")

            # Adjust positions to account for chunk offset
            adjusted_entities = []
            for entity in entities:
                adjusted = PHIEntity(
                    type=entity.type,
                    text=entity.text,
                    start_pos=chunk_info.start_pos + entity.start_pos,
                    end_pos=chunk_info.start_pos + entity.end_pos,
                    confidence=entity.confidence,
                    custom_type=entity.custom_type if hasattr(entity, 'custom_type') else None,
                )
                adjusted_entities.append(adjusted)

            logger.debug(f"Chunk {chunk_info.chunk_id}: identified {len(adjusted_entities)} entities")
            return adjusted_entities

        except Exception as e:
            logger.error(f"PHI identification failed for chunk {chunk_info.chunk_id}: {e}")
            return []

    def _convert_result(self, chunk_result: ChunkResult) -> PHIChunkResult:
        """Convert ChunkResult to PHIChunkResult"""
        if chunk_result.success and chunk_result.output:
            output = chunk_result.output
            return PHIChunkResult(
                chunk_id=chunk_result.chunk_info.chunk_id,
                start_pos=chunk_result.chunk_info.start_pos,
                end_pos=chunk_result.chunk_info.end_pos,
                entities=output.get("entities", []),
                raw_text=output.get("raw_text", ""),
                success=True,
                processing_time_ms=chunk_result.processing_time_ms,
                tool_calls_made=output.get("tool_calls", 0),
                rag_used=output.get("rag_used", False),
            )
        else:
            return PHIChunkResult(
                chunk_id=chunk_result.chunk_info.chunk_id,
                start_pos=chunk_result.chunk_info.start_pos,
                end_pos=chunk_result.chunk_info.end_pos,
                entities=[],
                raw_text="",
                success=False,
                error=chunk_result.error,
                processing_time_ms=chunk_result.processing_time_ms,
            )

    def _output_result(self, chunk_result: ChunkResult) -> None:
        """Output result immediately (called after each chunk)"""
        if self._output_file and chunk_result.success:
            phi_result = self._convert_result(chunk_result)
            self._output_file.write(json.dumps(phi_result.to_dict(), ensure_ascii=False))
            self._output_file.write("\n")
            self._output_file.flush()

    def get_progress(self, file_path: str) -> dict[str, Any] | None:
        """Get processing progress for a file"""
        return self._processor.get_progress(file_path)

    def reset_checkpoint(self, file_path: str) -> bool:
        """Reset checkpoint for a file"""
        return self._processor.reset_checkpoint(file_path)

    # RAG switch
    def enable_rag(self) -> None:
        """Enable RAG"""
        self.config.enable_rag = True
        logger.info("RAG enabled")

    def disable_rag(self) -> None:
        """Disable RAG"""
        self.config.enable_rag = False
        logger.info("RAG disabled")

    # Tool switch
    def enable_tools(self) -> None:
        """Enable tool calling"""
        self.config.enable_tools = True
        logger.info("Tools enabled")

    def disable_tools(self) -> None:
        """Disable tool calling"""
        self.config.enable_tools = False
        logger.info("Tools disabled")
