"""
Base Node | 基礎節點

Abstract base class for all chain nodes with:
- Tool-calling capability
- Streaming support
- Configurable behavior

所有 chain 節點的抽象基類，具有：
- 工具呼叫能力
- 串流支援
- 可配置行為
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from loguru import logger


class NodeStatus(str, Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class NodeConfig:
    """
    Configuration for a chain node
    Chain 節點配置
    """
    # Tool calling
    enable_tools: bool = True
    tools: list[BaseTool] = field(default_factory=list)
    max_tool_calls: int = 10  # Max tool calls per invocation

    # Generation
    max_iterations: int = 100  # No hard limit, but safety cap
    stream: bool = False

    # Timeout
    timeout_seconds: float = 300.0  # 5 minutes default

    # Debug
    verbose: bool = False


@dataclass
class NodeResult:
    """
    Result from a node execution
    節點執行結果
    """
    status: NodeStatus
    output: Any
    messages: list[BaseMessage] = field(default_factory=list)
    tool_calls_made: int = 0
    iterations: int = 0
    duration_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == NodeStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "output": self.output,
            "tool_calls_made": self.tool_calls_made,
            "iterations": self.iterations,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


T = TypeVar('T')


class BaseNode(ABC, Generic[T]):
    """
    Abstract base class for chain nodes
    Chain 節點的抽象基類
    
    Features:
    - Tool-calling support (any node can call tools)
    - Streaming support (for long outputs)
    - Iteration support (no generation limit)
    - Configurable behavior
    
    Subclasses must implement:
    - process(): Main processing logic
    - get_name(): Node identifier
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        config: NodeConfig | None = None,
    ):
        """
        Initialize base node
        
        Args:
            llm: Language model (optional, some nodes don't need LLM)
            config: Node configuration
        """
        self.llm = llm
        self.config = config or NodeConfig()

        # Bind tools to LLM if available
        if llm and self.config.enable_tools and self.config.tools:
            try:
                self.llm_with_tools = llm.bind_tools(self.config.tools)
                logger.debug(f"{self.get_name()}: Bound {len(self.config.tools)} tools to LLM")
            except (AttributeError, NotImplementedError):
                self.llm_with_tools = llm
                logger.warning(f"{self.get_name()}: LLM does not support tool binding")
        else:
            self.llm_with_tools = llm

    @abstractmethod
    def get_name(self) -> str:
        """Get node name for logging and identification"""
        pass

    @abstractmethod
    def process(self, input_data: dict[str, Any]) -> T:
        """
        Main processing logic
        
        Args:
            input_data: Input from previous node or initial input
            
        Returns:
            Processed output of type T
        """
        pass

    def invoke(self, input_data: dict[str, Any]) -> NodeResult:
        """
        Execute the node with full lifecycle management
        執行節點，包含完整生命週期管理
        
        This handles:
        - Timing
        - Error handling
        - Tool calling loop
        - Iteration management
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            NodeResult with status, output, and metadata
        """
        start_time = time.time()
        iterations = 0
        tool_calls = 0
        messages: list[BaseMessage] = []

        try:
            # Run main processing with iteration loop
            output = None

            while iterations < self.config.max_iterations:
                iterations += 1

                if self.config.verbose:
                    logger.debug(f"{self.get_name()}: Iteration {iterations}")

                # Process
                result = self.process(input_data)

                # Check if we need to handle tool calls
                if self._needs_tool_call(result):
                    if tool_calls >= self.config.max_tool_calls:
                        logger.warning(f"{self.get_name()}: Max tool calls reached ({self.config.max_tool_calls})")
                        break

                    # Execute tool calls
                    tool_results = self._execute_tool_calls(result)
                    tool_calls += len(tool_results)

                    # Add to input for next iteration
                    input_data = self._merge_tool_results(input_data, tool_results)
                    messages.extend(tool_results)
                    continue

                # No more tool calls needed
                output = result
                break

            duration_ms = (time.time() - start_time) * 1000

            return NodeResult(
                status=NodeStatus.COMPLETED,
                output=output,
                messages=messages,
                tool_calls_made=tool_calls,
                iterations=iterations,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"{self.get_name()}: Error - {e}")

            return NodeResult(
                status=NodeStatus.ERROR,
                output=None,
                messages=messages,
                tool_calls_made=tool_calls,
                iterations=iterations,
                duration_ms=duration_ms,
                error=str(e),
            )

    def stream(self, input_data: dict[str, Any]) -> Iterator[Any]:
        """
        Stream output for long generations
        串流輸出用於長生成
        
        Yields partial results as they become available.
        """
        if not self.config.stream:
            # Non-streaming: yield single result
            result = self.invoke(input_data)
            yield result
            return

        # Streaming implementation
        # Subclasses can override for custom streaming
        for chunk in self._stream_process(input_data):
            yield chunk

    def _stream_process(self, input_data: dict[str, Any]) -> Iterator[Any]:
        """Override in subclass for custom streaming"""
        yield self.process(input_data)

    def _needs_tool_call(self, result: Any) -> bool:
        """Check if result contains tool calls that need execution"""
        if isinstance(result, AIMessage):
            return bool(getattr(result, 'tool_calls', None))
        return False

    def _execute_tool_calls(self, result: Any) -> list[ToolMessage]:
        """Execute tool calls from LLM response"""
        if not isinstance(result, AIMessage):
            return []

        tool_calls = getattr(result, 'tool_calls', [])
        if not tool_calls:
            return []

        messages = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            # Find and execute tool
            tool_result = self._run_tool(tool_name, tool_args)

            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_id,
            ))

            if self.config.verbose:
                logger.debug(f"{self.get_name()}: Tool {tool_name} returned: {str(tool_result)[:100]}...")

        return messages

    def _run_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Execute a specific tool by name"""
        for tool in self.config.tools:
            if tool.name == tool_name:
                try:
                    return tool.invoke(tool_args)
                except Exception as e:
                    logger.error(f"{self.get_name()}: Tool {tool_name} failed: {e}")
                    return f"Tool error: {e!s}"

        return f"Unknown tool: {tool_name}"

    def _merge_tool_results(
        self,
        input_data: dict[str, Any],
        tool_messages: list[ToolMessage]
    ) -> dict[str, Any]:
        """Merge tool results back into input for next iteration"""
        new_input = dict(input_data)

        # Add tool results to messages
        existing_messages = new_input.get("messages", [])
        new_input["messages"] = existing_messages + tool_messages

        # Also add as structured data
        tool_results = new_input.get("tool_results", [])
        for msg in tool_messages:
            tool_results.append({
                "tool_call_id": msg.tool_call_id,
                "content": msg.content,
            })
        new_input["tool_results"] = tool_results

        return new_input

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()})"
