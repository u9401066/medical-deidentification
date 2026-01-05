"""
Base Tool for PHI Detection | PHI 檢測基礎工具

Defines the base class and data structures for all PHI detection tools.
定義所有 PHI 檢測工具的基礎類別和資料結構。

Design Principles:
1. Tools are fast (< 0.01s per chunk)
2. Tools are stateless (can be pickled for multiprocessing)
3. Tools return structured results
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import PHIType from domain layer - DDD principle: reuse domain types
# 從 domain 層匯入 PHIType - DDD 原則：重用領域類型
from core.domain.phi_types import PHIType


@dataclass
class ToolResult:
    """
    Result from a single tool detection
    單個工具檢測的結果
    
    Attributes:
        text: The detected PHI text
        phi_type: Type of PHI detected
        start_pos: Start position in original text
        end_pos: End position in original text
        confidence: Confidence score (0.0 - 1.0)
        tool_name: Name of the tool that detected this
        metadata: Additional metadata from the tool
    """
    text: str
    phi_type: PHIType
    start_pos: int
    end_pos: int
    confidence: float = 0.9
    tool_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.text, self.phi_type, self.start_pos))
    
    def __eq__(self, other):
        if not isinstance(other, ToolResult):
            return False
        return (
            self.text == other.text 
            and self.phi_type == other.phi_type 
            and self.start_pos == other.start_pos
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "phi_type": self.phi_type.value if isinstance(self.phi_type, PHIType) else self.phi_type,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "tool_name": self.tool_name,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ToolResult":
        """Create from dictionary."""
        phi_type = d.get("phi_type", "OTHER")
        if isinstance(phi_type, str):
            try:
                phi_type = PHIType(phi_type)
            except ValueError:
                phi_type = PHIType.OTHER
        
        return cls(
            text=d.get("text", ""),
            phi_type=phi_type,
            start_pos=d.get("start_pos", -1),
            end_pos=d.get("end_pos", -1),
            confidence=d.get("confidence", 0.9),
            tool_name=d.get("tool_name", ""),
            metadata=d.get("metadata", {}),
        )


class BasePHITool(ABC):
    """
    Base class for all PHI detection tools
    所有 PHI 檢測工具的基礎類別
    
    All tools must implement the `scan` method which takes text
    and returns a list of ToolResult objects.
    
    所有工具必須實現 `scan` 方法，接受文本並返回 ToolResult 列表。
    
    Example:
        class MyTool(BasePHITool):
            @property
            def name(self) -> str:
                return "my_tool"
            
            @property
            def supported_types(self) -> List[PHIType]:
                return [PHIType.NAME]
            
            def scan(self, text: str) -> List[ToolResult]:
                # Detection logic here
                return results
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name (used for logging and identification)
        工具名稱（用於日誌和識別）
        """
        pass
    
    @property
    @abstractmethod
    def supported_types(self) -> List[PHIType]:
        """
        List of PHI types this tool can detect
        此工具可檢測的 PHI 類型列表
        """
        pass
    
    @abstractmethod
    def scan(self, text: str) -> List[ToolResult]:
        """
        Scan text and return detected PHI
        掃描文本並返回檢測到的 PHI
        
        Args:
            text: Text to scan
            
        Returns:
            List of ToolResult objects
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __str__(self) -> str:
        return self.name


def merge_results(results: List[ToolResult]) -> List[ToolResult]:
    """
    Merge overlapping results, keeping the one with highest confidence
    合併重疊的結果，保留信心度最高的
    
    Args:
        results: List of ToolResult to merge
        
    Returns:
        Deduplicated list of ToolResult
    """
    if not results:
        return []
    
    # Sort by start position
    sorted_results = sorted(results, key=lambda r: (r.start_pos, -r.confidence))
    
    merged = []
    current = sorted_results[0]
    
    for result in sorted_results[1:]:
        # Check if overlapping
        if result.start_pos < current.end_pos:
            # Overlapping - keep the one with higher confidence
            if result.confidence > current.confidence:
                current = result
            # If same confidence, keep the longer one
            elif result.confidence == current.confidence:
                if (result.end_pos - result.start_pos) > (current.end_pos - current.start_pos):
                    current = result
        else:
            # No overlap - add current and move to next
            merged.append(current)
            current = result
    
    # Don't forget the last one
    merged.append(current)
    
    return merged
