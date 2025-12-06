"""
PHI Detection Tools Module | PHI 檢測工具模組

Fast, parallel PHI detection tools that run before LLM.
Tools use multiprocessing to bypass Python GIL limitation.

快速、並行的 PHI 檢測工具，在 LLM 之前執行。
工具使用多進程繞過 Python GIL 限制。

Phase 1 Tools:
- RegexPHITool: Pattern-based detection (ID, phone, email, date)
- IDValidatorTool: Taiwan ID validation with checksum
- PhoneTool: Phone number detection
- SpaCyNERTool: Named Entity Recognition

Usage:
    from medical_deidentification.infrastructure.tools import (
        ToolRunner,
        RegexPHITool,
        IDValidatorTool,
        PhoneTool,
        SpaCyNERTool,
    )
    
    # Create runner with tools
    runner = ToolRunner([
        RegexPHITool(),
        IDValidatorTool(),
        PhoneTool(),
    ])
    
    # Run on text
    results = runner.run_all("Patient ID: A123456789, Phone: 0912-345-678")
"""

from .base_tool import BasePHITool, ToolResult
from .tool_runner import ToolRunner
from .regex_phi_tool import RegexPHITool
from .id_validator_tool import IDValidatorTool
from .phone_tool import PhoneTool

# SpaCy tool is optional (requires spacy to be installed)
try:
    from .spacy_ner_tool import SpaCyNERTool
    SPACY_AVAILABLE = True
except ImportError:
    SpaCyNERTool = None
    SPACY_AVAILABLE = False

__all__ = [
    # Base
    "BasePHITool",
    "ToolResult",
    "ToolRunner",
    # Tools
    "RegexPHITool",
    "IDValidatorTool",
    "PhoneTool",
    "SpaCyNERTool",
    # Flags
    "SPACY_AVAILABLE",
]
