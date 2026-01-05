"""
Streaming Chunk Processor | 串流分塊處理器

FIFO stateless chunk processing for unlimited file sizes:
- Process one chunk at a time (avoid OOM)
- Checkpoint support for resume
- No accumulation in memory

無限檔案大小的 FIFO 無狀態分塊處理：
- 一次處理一個 chunk（避免 OOM）
- 支援斷點續處理
- 不在記憶體中累積

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │                   Large File                         │
    └─────────────────────────────────────────────────────┘
                            │
                            ▼ (chunk iterator)
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Chunk 1 │ → │ Chunk 2 │ → │ Chunk N │  (FIFO, one at a time)
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Process │   │ Process │   │ Process │  (stateless)
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │  Write  │   │  Write  │   │  Write  │  (immediate output)
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         ▼             ▼             ▼
    [Checkpoint 1] [Checkpoint 2] [Checkpoint N]  (resume support)
"""

import hashlib
import json
import os
from collections.abc import Callable, Generator, Iterator
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
)

from loguru import logger

T = TypeVar('T')


@dataclass
class ChunkInfo:
    """Information about a single chunk"""
    chunk_id: int
    start_pos: int
    end_pos: int
    size: int
    content_hash: str  # For verification

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChunkInfo":
        return cls(**d)


@dataclass
class ProcessingCheckpoint:
    """
    Checkpoint for resume capability
    斷點續處理的檢查點
    """
    # File info
    file_path: str
    file_hash: str  # To detect file changes
    total_size: int

    # Progress
    last_completed_chunk: int = -1  # -1 means not started
    total_chunks: int = 0
    processed_chunks: list[int] = field(default_factory=list)

    # Timing
    started_at: str = ""
    last_updated_at: str = ""

    # Configuration (to ensure consistency on resume)
    chunk_size: int = 0
    chunk_overlap: int = 0

    # Output tracking
    output_file: str = ""

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ProcessingCheckpoint":
        return cls(**d)

    def save(self, checkpoint_path: str) -> None:
        """Save checkpoint to file"""
        self.last_updated_at = datetime.now().isoformat()
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.debug(f"Checkpoint saved: chunk {self.last_completed_chunk}/{self.total_chunks}")

    @classmethod
    def load(cls, checkpoint_path: str) -> Optional["ProcessingCheckpoint"]:
        """Load checkpoint from file"""
        if not os.path.exists(checkpoint_path):
            return None
        try:
            with open(checkpoint_path, encoding='utf-8') as f:
                return cls.from_dict(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    @property
    def progress_percent(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        return (len(self.processed_chunks) / self.total_chunks) * 100

    @property
    def is_complete(self) -> bool:
        return len(self.processed_chunks) >= self.total_chunks


@dataclass
class ChunkResult:
    """Result from processing a single chunk"""
    chunk_info: ChunkInfo
    success: bool
    output: Any
    error: str | None = None
    processing_time_ms: float = 0.0


class StreamingChunkProcessor(Generic[T]):
    """
    FIFO Stateless Streaming Chunk Processor
    FIFO 無狀態串流分塊處理器
    
    Key features:
    - Process unlimited file sizes
    - One chunk in memory at a time
    - Checkpoint/resume support
    - Immediate output (no accumulation)
    
    主要特點：
    - 處理無限大檔案
    - 記憶體中一次只有一個 chunk
    - 支援斷點續處理
    - 立即輸出（不累積）
    
    Usage:
        processor = StreamingChunkProcessor(
            chunk_size=1000,
            process_func=my_phi_detector,
            output_func=write_to_file,
        )
        
        # Process with auto-resume
        for result in processor.process_file("large_file.txt"):
            print(f"Chunk {result.chunk_info.chunk_id}: {result.success}")
        
        # Or manually control
        processor.process_file_with_checkpoint(
            "large_file.txt",
            checkpoint_dir="./checkpoints"
        )
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 100,
        process_func: Callable[[str, ChunkInfo], T] | None = None,
        output_func: Callable[[ChunkResult], None] | None = None,
        checkpoint_dir: str | None = None,
        checkpoint_interval: int = 1,  # Save checkpoint every N chunks
    ):
        """
        Initialize streaming processor
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks (for context continuity)
            process_func: Function to process each chunk
            output_func: Function to output results (called immediately)
            checkpoint_dir: Directory for checkpoint files
            checkpoint_interval: Save checkpoint every N chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.process_func = process_func
        self.output_func = output_func
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_interval = checkpoint_interval

        # Create checkpoint directory if specified
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)

    def chunk_iterator(
        self,
        file_path: str,
        start_chunk: int = 0
    ) -> Generator[tuple[str, ChunkInfo], None, None]:
        """
        Iterate over file chunks without loading entire file
        迭代檔案分塊，不載入整個檔案
        
        Yields:
            Tuple of (chunk_content, chunk_info)
        """
        file_size = os.path.getsize(file_path)
        chunk_id = 0
        position = 0

        with open(file_path, encoding='utf-8') as f:
            while position < file_size:
                # Skip to position (accounting for previous chunks)
                if chunk_id < start_chunk:
                    # Calculate position for start_chunk
                    skip_to = start_chunk * (self.chunk_size - self.chunk_overlap)
                    f.seek(skip_to)
                    position = skip_to
                    chunk_id = start_chunk
                    continue

                # Read chunk
                chunk_start = position
                content = f.read(self.chunk_size)

                if not content:
                    break

                chunk_end = chunk_start + len(content)

                # Calculate content hash for verification
                content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

                chunk_info = ChunkInfo(
                    chunk_id=chunk_id,
                    start_pos=chunk_start,
                    end_pos=chunk_end,
                    size=len(content),
                    content_hash=content_hash,
                )

                yield content, chunk_info

                # Move position (with overlap)
                position = chunk_end - self.chunk_overlap
                if position <= chunk_start:  # Avoid infinite loop
                    position = chunk_end

                chunk_id += 1

                # Free memory hint
                del content

    def chunk_text_iterator(
        self,
        text: str,
        start_chunk: int = 0
    ) -> Generator[tuple[str, ChunkInfo], None, None]:
        """
        Iterate over text string in chunks
        分塊迭代文本字串
        """
        text_size = len(text)
        chunk_id = 0
        position = 0

        # Skip to start_chunk
        if start_chunk > 0:
            position = start_chunk * (self.chunk_size - self.chunk_overlap)
            chunk_id = start_chunk

        while position < text_size:
            chunk_start = position
            chunk_end = min(position + self.chunk_size, text_size)
            content = text[chunk_start:chunk_end]

            if not content:
                break

            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                start_pos=chunk_start,
                end_pos=chunk_end,
                size=len(content),
                content_hash=content_hash,
            )

            yield content, chunk_info

            # Move position (with overlap)
            position = chunk_end - self.chunk_overlap
            if position <= chunk_start:
                position = chunk_end

            chunk_id += 1

    def process_stream(
        self,
        chunk_iterator: Iterator[tuple[str, ChunkInfo]],
        checkpoint: ProcessingCheckpoint | None = None,
    ) -> Generator[ChunkResult, None, None]:
        """
        Process chunks from iterator (FIFO, stateless)
        從迭代器處理分塊（FIFO，無狀態）
        
        Each chunk is:
        1. Processed independently
        2. Output immediately
        3. Released from memory
        
        Yields:
            ChunkResult for each processed chunk
        """
        import time

        for content, chunk_info in chunk_iterator:
            # Skip already processed chunks (for resume)
            if checkpoint and chunk_info.chunk_id in checkpoint.processed_chunks:
                logger.debug(f"Skipping already processed chunk {chunk_info.chunk_id}")
                continue

            start_time = time.time()

            try:
                # Process chunk (stateless)
                if self.process_func:
                    output = self.process_func(content, chunk_info)
                else:
                    output = content  # Pass-through if no process function

                processing_time = (time.time() - start_time) * 1000

                result = ChunkResult(
                    chunk_info=chunk_info,
                    success=True,
                    output=output,
                    processing_time_ms=processing_time,
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                logger.error(f"Chunk {chunk_info.chunk_id} processing failed: {e}")

                result = ChunkResult(
                    chunk_info=chunk_info,
                    success=False,
                    output=None,
                    error=str(e),
                    processing_time_ms=processing_time,
                )

            # Output immediately (don't accumulate)
            if self.output_func:
                try:
                    self.output_func(result)
                except Exception as e:
                    logger.error(f"Output function failed: {e}")

            # Update checkpoint
            if checkpoint:
                checkpoint.processed_chunks.append(chunk_info.chunk_id)
                checkpoint.last_completed_chunk = chunk_info.chunk_id

                # Save checkpoint at interval
                if (chunk_info.chunk_id + 1) % self.checkpoint_interval == 0:
                    if self.checkpoint_dir:
                        checkpoint_path = self._get_checkpoint_path(checkpoint.file_path)
                        checkpoint.save(checkpoint_path)

            # Yield result
            yield result

            # Explicitly release memory
            del content

            logger.debug(
                f"Chunk {chunk_info.chunk_id} processed in {processing_time:.1f}ms"
            )

    def process_file(
        self,
        file_path: str,
        resume: bool = True,
    ) -> Generator[ChunkResult, None, None]:
        """
        Process file with automatic checkpoint/resume
        處理檔案，自動支援斷點續處理
        
        Args:
            file_path: Path to file to process
            resume: Whether to resume from checkpoint if available
            
        Yields:
            ChunkResult for each chunk
        """
        # Calculate file hash for verification
        file_hash = self._calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)

        # Check for existing checkpoint
        checkpoint = None
        start_chunk = 0

        if resume and self.checkpoint_dir:
            checkpoint_path = self._get_checkpoint_path(file_path)
            checkpoint = ProcessingCheckpoint.load(checkpoint_path)

            if checkpoint:
                # Verify file hasn't changed
                if checkpoint.file_hash != file_hash:
                    logger.warning("File has changed since last checkpoint, starting fresh")
                    checkpoint = None
                elif checkpoint.chunk_size != self.chunk_size:
                    logger.warning("Chunk size changed, starting fresh")
                    checkpoint = None
                else:
                    start_chunk = checkpoint.last_completed_chunk + 1
                    logger.info(
                        f"Resuming from chunk {start_chunk}, "
                        f"{checkpoint.progress_percent:.1f}% complete"
                    )

        # Create new checkpoint if needed
        if checkpoint is None:
            total_chunks = self._estimate_total_chunks(file_size)
            checkpoint = ProcessingCheckpoint(
                file_path=file_path,
                file_hash=file_hash,
                total_size=file_size,
                total_chunks=total_chunks,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                started_at=datetime.now().isoformat(),
            )

        # Process chunks
        chunk_iter = self.chunk_iterator(file_path, start_chunk)

        for result in self.process_stream(chunk_iter, checkpoint):
            yield result

        # Save final checkpoint
        if self.checkpoint_dir:
            checkpoint_path = self._get_checkpoint_path(file_path)
            checkpoint.save(checkpoint_path)

            if checkpoint.is_complete:
                logger.success(f"Processing complete: {file_path}")

    def process_text(
        self,
        text: str,
        text_id: str = "text",
        resume: bool = True,
    ) -> Generator[ChunkResult, None, None]:
        """
        Process text string with checkpoint support
        處理文本字串，支援斷點續處理
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Check for checkpoint
        checkpoint = None
        start_chunk = 0

        if resume and self.checkpoint_dir:
            checkpoint_path = os.path.join(self.checkpoint_dir, f"{text_id}.checkpoint.json")
            checkpoint = ProcessingCheckpoint.load(checkpoint_path)

            if checkpoint and checkpoint.file_hash == text_hash:
                start_chunk = checkpoint.last_completed_chunk + 1
                logger.info(f"Resuming text processing from chunk {start_chunk}")
            else:
                checkpoint = None

        if checkpoint is None:
            total_chunks = self._estimate_total_chunks(len(text))
            checkpoint = ProcessingCheckpoint(
                file_path=text_id,
                file_hash=text_hash,
                total_size=len(text),
                total_chunks=total_chunks,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                started_at=datetime.now().isoformat(),
            )

        chunk_iter = self.chunk_text_iterator(text, start_chunk)

        for result in self.process_stream(chunk_iter, checkpoint):
            yield result

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file for change detection"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Only hash first 1MB for speed
            hasher.update(f.read(1024 * 1024))
        return hasher.hexdigest()

    def _estimate_total_chunks(self, total_size: int) -> int:
        """Estimate total number of chunks"""
        if self.chunk_size <= self.chunk_overlap:
            return total_size  # Fallback
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        return (total_size + effective_chunk_size - 1) // effective_chunk_size

    def _get_checkpoint_path(self, file_path: str) -> str:
        """Get checkpoint file path for a given input file"""
        if not self.checkpoint_dir:
            return ""
        file_name = os.path.basename(file_path)
        return os.path.join(self.checkpoint_dir, f"{file_name}.checkpoint.json")

    def get_progress(self, file_path: str) -> dict[str, Any] | None:
        """Get processing progress for a file"""
        if not self.checkpoint_dir:
            return None

        checkpoint_path = self._get_checkpoint_path(file_path)
        checkpoint = ProcessingCheckpoint.load(checkpoint_path)

        if checkpoint:
            return {
                "progress_percent": checkpoint.progress_percent,
                "processed_chunks": len(checkpoint.processed_chunks),
                "total_chunks": checkpoint.total_chunks,
                "is_complete": checkpoint.is_complete,
                "started_at": checkpoint.started_at,
                "last_updated_at": checkpoint.last_updated_at,
            }
        return None

    def reset_checkpoint(self, file_path: str) -> bool:
        """Reset/delete checkpoint for a file"""
        if not self.checkpoint_dir:
            return False

        checkpoint_path = self._get_checkpoint_path(file_path)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            logger.info(f"Checkpoint reset: {file_path}")
            return True
        return False
