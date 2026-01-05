"""
Regex-based PHI Detection Tool | 正則表達式 PHI 檢測工具

Fast regex patterns for common PHI types.
使用快速正則表達式檢測常見 PHI 類型。

Patterns cover:
- Taiwan National ID (身份證字號)
- Email addresses
- URLs
- IP addresses
- Dates (multiple formats)
"""

import re
from re import Pattern

from core.domain.phi_types import PHIType
from core.infrastructure.tools.base_tool import BasePHITool, ToolResult


class RegexPHITool(BasePHITool):
    """
    Regex-based PHI detection tool
    基於正則表達式的 PHI 檢測工具
    
    Features:
    - Pre-compiled patterns for performance
    - Configurable patterns per PHI type
    - Low false-positive rate
    
    Usage:
        tool = RegexPHITool()
        results = tool.scan("Contact: test@example.com")
    """

    # Pre-compiled regex patterns for each PHI type
    # 每種 PHI 類型的預編譯正則表達式
    DEFAULT_PATTERNS: dict[PHIType, list[tuple[Pattern, float]]] = {
        # Taiwan National ID: A123456789 format
        # 台灣身份證: [A-Z][12]\d{8}
        PHIType.ID: [
            (re.compile(r'\b[A-Z][12]\d{8}\b'), 0.95),  # Taiwan ID
            (re.compile(r'\b[A-Z]{2}\d{8,10}\b'), 0.8),  # ARC (居留證)
        ],

        # Email addresses
        PHIType.EMAIL: [
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), 0.95),
        ],

        # URLs
        PHIType.URL: [
            (re.compile(r'https?://[^\s<>"]+'), 0.95),
            (re.compile(r'www\.[^\s<>"]+'), 0.90),
        ],

        # IP addresses
        PHIType.IP_ADDRESS: [
            # IPv4
            (re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'), 0.95),
            # IPv6 (simplified)
            (re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'), 0.90),
        ],

        # Dates - multiple formats
        # 日期 - 多種格式
        PHIType.DATE: [
            # YYYY-MM-DD, YYYY/MM/DD
            (re.compile(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'), 0.90),
            # MM-DD-YYYY, MM/DD/YYYY
            (re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b'), 0.85),
            # Chinese date: 民國112年3月5日, 2024年3月5日
            (re.compile(r'(?:民國)?\d{2,4}年\d{1,2}月\d{1,2}日'), 0.90),
            # English date: March 5, 2024
            (re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE), 0.85),
        ],

        # Medical Record Numbers (common patterns)
        # 病歷號 (常見格式)
        PHIType.MEDICAL_RECORD_NUMBER: [
            # Common hospital MRN formats: 12345678, H12345678
            (re.compile(r'\b[A-Z]?\d{7,10}\b'), 0.70),  # Lower confidence - too general
        ],

        # Account numbers
        PHIType.ACCOUNT_NUMBER: [
            # Bank account patterns (Taiwan)
            (re.compile(r'\b\d{3}-\d{2}-\d{6,7}-\d\b'), 0.85),
            # General account number
            (re.compile(r'\b\d{10,16}\b'), 0.60),  # Very low confidence - could be many things
        ],

        # Fax numbers (same patterns as phone but with fax keywords nearby)
        PHIType.FAX: [
            (re.compile(r'(?:傳真|fax)[^\d]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4})', re.IGNORECASE), 0.90),
        ],

        # Location patterns (simplified)
        PHIType.LOCATION: [
            # Taiwan address patterns
            (re.compile(r'[\u4e00-\u9fff]{2,4}(?:市|縣)[\u4e00-\u9fff]{2,4}(?:區|鎮|鄉)'), 0.80),
            # Zip code + address
            (re.compile(r'\b\d{3,5}\s*[\u4e00-\u9fff]+(?:市|縣|區|路|街|巷|弄|號)'), 0.85),
        ],
    }

    def __init__(self, custom_patterns: dict[PHIType, list[tuple[Pattern, float]]] | None = None):
        """
        Initialize regex tool with optional custom patterns
        使用可選的自定義模式初始化正則工具
        
        Args:
            custom_patterns: Additional patterns to merge with defaults
        """
        self._patterns = dict(self.DEFAULT_PATTERNS)
        if custom_patterns:
            for phi_type, patterns in custom_patterns.items():
                if phi_type in self._patterns:
                    self._patterns[phi_type].extend(patterns)
                else:
                    self._patterns[phi_type] = patterns

    @property
    def name(self) -> str:
        return "regex_phi_tool"

    @property
    def supported_types(self) -> list[PHIType]:
        return list(self._patterns.keys())

    def scan(self, text: str) -> list[ToolResult]:
        """
        Scan text using regex patterns
        使用正則表達式掃描文本
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected PHI
        """
        results = []

        for phi_type, patterns in self._patterns.items():
            for pattern, confidence in patterns:
                for match in pattern.finditer(text):
                    # For patterns with groups, use the first group if available
                    matched_text = match.group(1) if match.groups() else match.group(0)
                    start = match.start(1) if match.groups() else match.start()
                    end = match.end(1) if match.groups() else match.end()

                    results.append(ToolResult(
                        text=matched_text,
                        phi_type=phi_type,
                        start_pos=start,
                        end_pos=end,
                        confidence=confidence,
                        tool_name=self.name,
                        metadata={
                            "pattern": pattern.pattern,
                        }
                    ))

        return results

    def scan_type(self, text: str, phi_type: PHIType) -> list[ToolResult]:
        """
        Scan text for a specific PHI type only
        僅掃描特定 PHI 類型
        
        Args:
            text: Text to scan
            phi_type: Specific PHI type to detect
            
        Returns:
            List of detected PHI of the specified type
        """
        results = []

        if phi_type not in self._patterns:
            return results

        for pattern, confidence in self._patterns[phi_type]:
            for match in pattern.finditer(text):
                matched_text = match.group(1) if match.groups() else match.group(0)
                start = match.start(1) if match.groups() else match.start()
                end = match.end(1) if match.groups() else match.end()

                results.append(ToolResult(
                    text=matched_text,
                    phi_type=phi_type,
                    start_pos=start,
                    end_pos=end,
                    confidence=confidence,
                    tool_name=self.name,
                    metadata={
                        "pattern": pattern.pattern,
                    }
                ))

        return results
