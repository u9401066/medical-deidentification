"""
Phone Number Detection Tool | 電話號碼檢測工具

Detects phone numbers with format validation and region detection.
檢測電話號碼，支援格式驗證和地區識別。

Supported formats:
- Taiwan landline: 02-1234-5678, (02) 12345678
- Taiwan mobile: 0912-345-678, 0912345678
- International: +886-2-1234-5678
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from core.domain.phi_types import PHIType
from core.infrastructure.tools.base_tool import BasePHITool, ToolResult


@dataclass
class PhonePattern:
    """Phone number pattern configuration"""
    pattern: re.Pattern
    phone_type: str
    region: str
    confidence: float


class PhoneTool(BasePHITool):
    """
    Phone number detection tool
    電話號碼檢測工具
    
    Features:
    - Detects Taiwan landline and mobile numbers
    - Supports various formats (with/without separators)
    - Detects international format (+886)
    - Context-aware (ignores numbers in irrelevant contexts)
    
    Usage:
        tool = PhoneTool()
        results = tool.scan("聯絡電話: 02-1234-5678")
    """
    
    def __init__(self):
        """Initialize phone detection patterns"""
        self._patterns: List[PhonePattern] = [
            # Taiwan mobile: 09XX-XXX-XXX or 09XXXXXXXX
            PhonePattern(
                pattern=re.compile(r'\b09\d{2}[-\s]?\d{3}[-\s]?\d{3}\b'),
                phone_type="MOBILE",
                region="TW",
                confidence=0.95,
            ),
            # Taiwan landline with area code: 0X-XXXX-XXXX or (0X) XXXXXXXX
            PhonePattern(
                pattern=re.compile(r'\(0[2-9]\)\s?\d{4}[-\s]?\d{4}\b'),
                phone_type="LANDLINE",
                region="TW",
                confidence=0.95,
            ),
            PhonePattern(
                pattern=re.compile(r'\b0[2-9][-\s]?\d{4}[-\s]?\d{4}\b'),
                phone_type="LANDLINE",
                region="TW",
                confidence=0.90,
            ),
            # Taiwan landline without area code (8 digits)
            PhonePattern(
                pattern=re.compile(r'\b[2-9]\d{3}[-\s]?\d{4}\b'),
                phone_type="LANDLINE",
                region="TW",
                confidence=0.70,  # Lower confidence without area code
            ),
            # International format: +886-X-XXXX-XXXX
            PhonePattern(
                pattern=re.compile(r'\+886[-\s]?[2-9][-\s]?\d{4}[-\s]?\d{4}\b'),
                phone_type="LANDLINE",
                region="TW",
                confidence=0.98,
            ),
            PhonePattern(
                pattern=re.compile(r'\+886[-\s]?9\d{2}[-\s]?\d{3}[-\s]?\d{3}\b'),
                phone_type="MOBILE",
                region="TW",
                confidence=0.98,
            ),
            # General international: +XX-XXX-XXXX-XXXX
            PhonePattern(
                pattern=re.compile(r'\+\d{1,3}[-\s]?\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b'),
                phone_type="INTERNATIONAL",
                region="UNKNOWN",
                confidence=0.85,
            ),
        ]
        
        # Context keywords that increase confidence
        self._phone_keywords = re.compile(
            r'(?:電話|手機|聯絡|連絡|phone|tel|mobile|cell|contact|fax|傳真)[\s:：]*',
            re.IGNORECASE
        )
        
        # Patterns to exclude (date-like patterns, ID-like patterns)
        self._exclusion_patterns = [
            re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}'),  # Date YYYY-MM-DD
            re.compile(r'[A-Z][12]\d{8}'),  # Taiwan ID
        ]
    
    @property
    def name(self) -> str:
        return "phone_tool"
    
    @property
    def supported_types(self) -> List[PHIType]:
        return [PHIType.PHONE, PHIType.FAX, PHIType.CONTACT]
    
    def scan(self, text: str) -> List[ToolResult]:
        """
        Scan text for phone numbers
        掃描文本中的電話號碼
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected phone numbers
        """
        results = []
        found_positions = set()  # Track found positions to avoid duplicates
        
        for phone_pattern in self._patterns:
            for match in phone_pattern.pattern.finditer(text):
                # Skip if this position was already found by a higher-confidence pattern
                if match.start() in found_positions:
                    continue
                
                phone_number = match.group(0)
                
                # Skip if matches exclusion pattern
                if self._should_exclude(phone_number):
                    continue
                
                # Calculate confidence based on context
                confidence = self._calculate_confidence(
                    text, match.start(), phone_pattern.confidence
                )
                
                # Determine if it's a fax number based on context
                phi_type = self._determine_phi_type(text, match.start())
                
                results.append(ToolResult(
                    text=phone_number,
                    phi_type=phi_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    tool_name=self.name,
                    metadata={
                        "phone_type": phone_pattern.phone_type,
                        "region": phone_pattern.region,
                        "normalized": self._normalize_phone(phone_number),
                    }
                ))
                
                # Mark this position as found
                for pos in range(match.start(), match.end()):
                    found_positions.add(pos)
        
        return results
    
    def _should_exclude(self, text: str) -> bool:
        """Check if text should be excluded (looks like date or ID)"""
        for pattern in self._exclusion_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _calculate_confidence(self, text: str, start_pos: int, base_confidence: float) -> float:
        """
        Calculate confidence based on surrounding context
        根據上下文計算信心度
        """
        # Look for phone keywords before the number
        context_start = max(0, start_pos - 20)
        context = text[context_start:start_pos]
        
        if self._phone_keywords.search(context):
            # Boost confidence if phone keyword found nearby
            return min(0.99, base_confidence + 0.05)
        
        return base_confidence
    
    def _determine_phi_type(self, text: str, start_pos: int) -> PHIType:
        """
        Determine if this is a phone or fax based on context
        根據上下文判斷是電話還是傳真
        """
        context_start = max(0, start_pos - 15)
        context = text[context_start:start_pos].lower()
        
        if 'fax' in context or '傳真' in context:
            return PHIType.FAX
        
        return PHIType.PHONE
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to digits only
        將電話號碼標準化為純數字
        """
        # Remove all non-digit characters except +
        normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
        return normalized
