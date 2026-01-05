"""
Tool Runner with Multiprocessing | 多進程工具執行器

Runs multiple PHI detection tools in parallel using multiprocessing
to bypass Python GIL limitation.

使用多進程並行運行多個 PHI 檢測工具，繞過 Python GIL 限制。

Key Features:
- Worker pool with preloaded models (SpaCy, etc.)
- Parallel execution across CPU cores
- Result merging with deduplication
- Graceful shutdown

Performance:
- Tool execution: ~0.01s per chunk
- 8 workers: Process 8 chunks in ~0.01s
"""

import multiprocessing as mp
from multiprocessing import Pool
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass
import time
import os

from loguru import logger

from .base_tool import BasePHITool, ToolResult, merge_results, PHIType


@dataclass
class WorkerTask:
    """
    Task for a worker to process
    工人處理的任務
    """
    text: str
    chunk_id: str = ""
    

@dataclass
class WorkerOutput:
    """
    Output from a worker
    工人的輸出
    """
    chunk_id: str
    results: List[Dict[str, Any]]  # Serialized ToolResults
    processing_time_ms: float
    error: Optional[str] = None


# Global worker state (initialized per worker process)
_worker_tools: Optional[List[BasePHITool]] = None


def _worker_init(tool_configs: List[Dict[str, Any]]) -> None:
    """
    Initialize worker process with tools
    使用工具初始化工作進程
    
    Called once when worker process starts.
    This is where we load heavy models like SpaCy.
    """
    global _worker_tools
    
    from .regex_phi_tool import RegexPHITool
    from .id_validator_tool import IDValidatorTool
    from .phone_tool import PhoneTool
    
    _worker_tools = []
    
    for config in tool_configs:
        tool_type = config.get("type", "")
        
        if tool_type == "regex":
            _worker_tools.append(RegexPHITool())
        elif tool_type == "id_validator":
            _worker_tools.append(IDValidatorTool())
        elif tool_type == "phone":
            _worker_tools.append(PhoneTool())
        elif tool_type == "spacy":
            try:
                from .spacy_ner_tool import SpaCyNERTool
                model_name = config.get("model", "zh_core_web_sm")
                _worker_tools.append(SpaCyNERTool(model_name=model_name))
            except ImportError:
                logger.warning("SpaCy not available, skipping SpaCyNERTool")
    
    logger.debug(f"Worker {os.getpid()} initialized with {len(_worker_tools)} tools")


def _worker_process(task: WorkerTask) -> WorkerOutput:
    """
    Process a single task in worker
    在工作進程中處理單個任務
    """
    global _worker_tools
    
    start_time = time.time()
    all_results = []
    error = None
    
    try:
        if _worker_tools is None:
            raise RuntimeError("Worker not initialized")
        
        for tool in _worker_tools:
            try:
                results = tool.scan(task.text)
                all_results.extend([r.to_dict() for r in results])
            except Exception as e:
                logger.warning(f"Tool {tool.name} failed: {e}")
    
    except Exception as e:
        error = str(e)
        logger.error(f"Worker error: {e}")
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    return WorkerOutput(
        chunk_id=task.chunk_id,
        results=all_results,
        processing_time_ms=elapsed_ms,
        error=error,
    )


class ToolRunner:
    """
    Runs PHI detection tools in parallel
    並行運行 PHI 檢測工具
    
    Uses multiprocessing to bypass GIL and achieve true parallelism.
    使用多進程繞過 GIL，實現真正的並行。
    
    Usage:
        # Option 1: With tool instances (single-process mode)
        runner = ToolRunner(tools=[RegexPHITool(), IDValidatorTool()])
        results = runner.run_all("Patient ID: A123456789")
        
        # Option 2: With multiprocessing (parallel mode)
        runner = ToolRunner.create_parallel(num_workers=4)
        results = runner.run_batch(["text1", "text2", "text3", ...])
        runner.shutdown()
    """
    
    def __init__(
        self,
        tools: Optional[List[BasePHITool]] = None,
        num_workers: int = 1,
    ):
        """
        Initialize ToolRunner
        
        Args:
            tools: List of tool instances (for single-process mode)
            num_workers: Number of worker processes (1 = no multiprocessing)
        """
        self.tools = tools or []
        self.num_workers = num_workers
        self._pool: Optional["Pool"] = None  # type: ignore
        self._initialized = False
    
    @classmethod
    def create_parallel(
        cls,
        num_workers: Optional[int] = None,
        include_spacy: bool = False,
        spacy_model: str = "zh_core_web_sm",
    ) -> "ToolRunner":
        """
        Create a parallel ToolRunner with multiprocessing
        創建並行 ToolRunner
        
        Args:
            num_workers: Number of workers (default: CPU count - 1)
            include_spacy: Include SpaCy NER tool
            spacy_model: SpaCy model name
            
        Returns:
            ToolRunner instance configured for parallel execution
        """
        if num_workers is None:
            num_workers = max(1, mp.cpu_count() - 1)
        
        runner = cls(tools=None, num_workers=num_workers)
        
        # Configure tool types for workers
        runner._tool_configs = [
            {"type": "regex"},
            {"type": "id_validator"},
            {"type": "phone"},
        ]
        
        if include_spacy:
            runner._tool_configs.append({
                "type": "spacy",
                "model": spacy_model,
            })
        
        return runner
    
    @classmethod
    def create_default(cls) -> "ToolRunner":
        """
        Create a default ToolRunner with standard tools (single-process)
        創建默認 ToolRunner（單進程）
        """
        from .regex_phi_tool import RegexPHITool
        from .id_validator_tool import IDValidatorTool
        from .phone_tool import PhoneTool
        
        return cls(tools=[
            RegexPHITool(),
            IDValidatorTool(),
            PhoneTool(),
        ])
    
    def _ensure_pool(self) -> None:
        """Ensure worker pool is initialized."""
        if self._pool is not None:
            return
        
        if self.num_workers <= 1:
            return
        
        if not hasattr(self, '_tool_configs'):
            # Create default configs from tools
            self._tool_configs = []
            for tool in self.tools:
                if "regex" in tool.name.lower():
                    self._tool_configs.append({"type": "regex"})
                elif "id" in tool.name.lower():
                    self._tool_configs.append({"type": "id_validator"})
                elif "phone" in tool.name.lower():
                    self._tool_configs.append({"type": "phone"})
                elif "spacy" in tool.name.lower():
                    self._tool_configs.append({"type": "spacy"})
        
        logger.info(f"Initializing worker pool with {self.num_workers} workers")
        
        # Use spawn context for Windows compatibility
        ctx = mp.get_context('spawn')
        self._pool = ctx.Pool(
            self.num_workers,
            initializer=_worker_init,
            initargs=(self._tool_configs,),
        )
        self._initialized = True
    
    def run_all(self, text: str) -> List[ToolResult]:
        """
        Run all tools on a single text (single-process)
        對單個文本運行所有工具（單進程）
        
        Args:
            text: Text to scan
            
        Returns:
            Merged list of ToolResult
        """
        all_results = []
        
        for tool in self.tools:
            try:
                results = tool.scan(text)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Tool {tool.name} failed: {e}")
        
        # Merge overlapping results
        return merge_results(all_results)
    
    def run_batch(
        self,
        texts: List[str],
        chunk_ids: Optional[List[str]] = None,
    ) -> Dict[str, List[ToolResult]]:
        """
        Run tools on batch of texts (parallel if num_workers > 1)
        對批量文本運行工具（如果 num_workers > 1 則並行）
        
        Args:
            texts: List of texts to scan
            chunk_ids: Optional list of chunk IDs
            
        Returns:
            Dict mapping chunk_id to list of ToolResult
        """
        if not texts:
            return {}
        
        # Generate chunk IDs if not provided
        if chunk_ids is None:
            chunk_ids = [f"chunk_{i}" for i in range(len(texts))]
        
        # Create tasks
        tasks = [
            WorkerTask(text=text, chunk_id=cid)
            for text, cid in zip(texts, chunk_ids)
        ]
        
        # Single-process mode
        if self.num_workers <= 1:
            results = {}
            for task in tasks:
                tool_results = self.run_all(task.text)
                results[task.chunk_id] = tool_results
            return results
        
        # Parallel mode
        self._ensure_pool()
        
        outputs: List[WorkerOutput] = self._pool.map(_worker_process, tasks)
        
        # Convert outputs to results
        results = {}
        for output in outputs:
            if output.error:
                logger.warning(f"Chunk {output.chunk_id} had error: {output.error}")
                results[output.chunk_id] = []
            else:
                tool_results = [ToolResult.from_dict(d) for d in output.results]
                results[output.chunk_id] = merge_results(tool_results)
        
        return results
    
    def shutdown(self) -> None:
        """
        Gracefully shutdown worker pool
        優雅關閉工作池
        """
        if self._pool is not None:
            logger.info("Shutting down worker pool")
            self._pool.close()
            self._pool.join()
            self._pool = None
            self._initialized = False
    
    def __enter__(self) -> "ToolRunner":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
    
    def __repr__(self) -> str:
        if self.tools:
            tool_names = [t.name for t in self.tools]
            return f"ToolRunner(tools={tool_names}, workers={self.num_workers})"
        return f"ToolRunner(workers={self.num_workers})"
