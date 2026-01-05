"""
PHI Chain Nodes Package | PHI Chain 節點套件

Modular chain architecture where:
- Each node is a separate file
- Any node can call tools
- Chain can extend indefinitely (no generation limit)
- RAG is configurable (on/off)

模組化 chain 架構：
- 每個節點獨立檔案
- 任意節點可呼叫工具
- Chain 可無限延伸
- RAG 可配置開關

Architecture:
    ┌─────────────┐
    │  BaseNode   │ ← Abstract base with tool-calling capability
    └──────┬──────┘
           │
    ┌──────┴──────────────────────────────────┐
    │                                          │
    ▼                                          ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ RAGNode    │  │AnalyzeNode │  │ToolNode    │  │ OutputNode │
│ (optional) │  │            │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘  └────────────┘

Chain Composition:
    PHIChain = RAGNode? → AnalyzeNode → ToolNode* → OutputNode
    (* = can repeat, ? = optional)
"""

from .analyze_node import AnalyzeNode
from .base_node import BaseNode, NodeConfig, NodeResult
from .output_node import OutputNode
from .phi_chain import PHIChain, PHIChainConfig
from .rag_node import RAGNode
from .tool_node import ToolNode

__all__ = [
    # Base
    "BaseNode",
    "NodeConfig",
    "NodeResult",
    # Nodes
    "RAGNode",
    "AnalyzeNode",
    "ToolNode",
    "OutputNode",
    # Chain
    "PHIChain",
    "PHIChainConfig",
]
