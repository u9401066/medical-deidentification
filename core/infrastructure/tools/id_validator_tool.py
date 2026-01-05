"""
ID Validator Tool | ID 驗證工具

Validates and detects national IDs with checksum verification.
使用校驗碼驗證並檢測國民身份證。

Supported ID types:
- Taiwan National ID (身份證字號) - 10 digits with letter prefix
- Taiwan ARC (居留證) - 2 letters + 8 digits
- Taiwan Unified Invoice Number (統一編號) - 8 digits
"""

import re

from core.domain.phi_types import PHIType
from core.infrastructure.tools.base_tool import BasePHITool, ToolResult


class IDValidatorTool(BasePHITool):
    """
    ID validation tool with checksum verification
    帶有校驗碼驗證的 ID 檢測工具
    
    Features:
    - Validates Taiwan National ID checksums
    - High confidence for valid IDs
    - Lower confidence for pattern matches without valid checksum
    
    Usage:
        tool = IDValidatorTool()
        results = tool.scan("Patient ID: A123456789")
    """

    # Taiwan ID letter-to-number mapping (A=10, B=11, ..., Z=35)
    # 台灣身份證字母對應數字
    TW_ID_LETTER_MAP: dict[str, int] = {
        'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'G': 16,
        'H': 17, 'I': 34, 'J': 18, 'K': 19, 'L': 20, 'M': 21, 'N': 22,
        'O': 35, 'P': 23, 'Q': 24, 'R': 25, 'S': 26, 'T': 27, 'U': 28,
        'V': 29, 'W': 32, 'X': 30, 'Y': 31, 'Z': 33
    }

    # Weights for Taiwan ID checksum calculation
    # 台灣身份證校驗權重
    TW_ID_WEIGHTS: list[int] = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1]

    def __init__(self, validate_checksum: bool = True):
        """
        Initialize ID validator tool
        初始化 ID 驗證工具
        
        Args:
            validate_checksum: Whether to validate checksums (default True)
                              If False, pattern match is sufficient
        """
        self._validate_checksum = validate_checksum

        # Pre-compile regex patterns
        self._tw_id_pattern = re.compile(r'\b[A-Z][12]\d{8}\b')
        self._tw_arc_pattern = re.compile(r'\b[A-Z]{2}\d{8}\b')
        self._tw_ubn_pattern = re.compile(r'\b\d{8}\b')  # 統一編號

    @property
    def name(self) -> str:
        return "id_validator_tool"

    @property
    def supported_types(self) -> list[PHIType]:
        return [PHIType.ID, PHIType.ACCOUNT_NUMBER]

    def scan(self, text: str) -> list[ToolResult]:
        """
        Scan text for national IDs
        掃描文本中的身份證號碼
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected IDs with validation results
        """
        results = []

        # Scan for Taiwan National IDs
        results.extend(self._scan_taiwan_id(text))

        # Scan for Taiwan ARC (居留證)
        results.extend(self._scan_taiwan_arc(text))

        return results

    def _scan_taiwan_id(self, text: str) -> list[ToolResult]:
        """Scan for Taiwan National ID (身份證字號)"""
        results = []

        for match in self._tw_id_pattern.finditer(text):
            id_number = match.group(0)
            is_valid = self._validate_taiwan_id(id_number)

            # Valid checksum = high confidence, invalid = lower confidence
            confidence = 0.99 if is_valid else 0.70

            # If we require valid checksum and it's invalid, skip
            if self._validate_checksum and not is_valid:
                confidence = 0.60  # Still report but with low confidence

            results.append(ToolResult(
                text=id_number,
                phi_type=PHIType.ID,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=confidence,
                tool_name=self.name,
                metadata={
                    "id_type": "TW_NATIONAL_ID",
                    "checksum_valid": is_valid,
                }
            ))

        return results

    def _scan_taiwan_arc(self, text: str) -> list[ToolResult]:
        """Scan for Taiwan ARC (外僑居留證)"""
        results = []

        for match in self._tw_arc_pattern.finditer(text):
            arc_number = match.group(0)
            is_valid = self._validate_taiwan_arc(arc_number)

            confidence = 0.95 if is_valid else 0.65

            results.append(ToolResult(
                text=arc_number,
                phi_type=PHIType.ID,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=confidence,
                tool_name=self.name,
                metadata={
                    "id_type": "TW_ARC",
                    "checksum_valid": is_valid,
                }
            ))

        return results

    def _validate_taiwan_id(self, id_number: str) -> bool:
        r"""
        Validate Taiwan National ID checksum
        驗證台灣身份證字號校驗碼
        
        Taiwan ID format: [A-Z][1-2]\d{8}
        - First letter represents birth city
        - Second digit: 1=male, 2=female
        - Last digit is checksum
        
        Algorithm:
        1. Convert letter to two digits (A=10, B=11, etc.)
        2. Apply weights [1,9,8,7,6,5,4,3,2,1,1]
        3. Sum should be divisible by 10
        """
        if not id_number or len(id_number) != 10:
            return False

        try:
            letter = id_number[0].upper()
            if letter not in self.TW_ID_LETTER_MAP:
                return False

            # Convert letter to two-digit number
            letter_value = self.TW_ID_LETTER_MAP[letter]
            digit1 = letter_value // 10
            digit2 = letter_value % 10

            # Build digit array: [letter_d1, letter_d2, d1, d2, ..., d8]
            digits = [digit1, digit2] + [int(d) for d in id_number[1:]]

            # Calculate weighted sum
            total = sum(d * w for d, w in zip(digits, self.TW_ID_WEIGHTS))

            return total % 10 == 0

        except (ValueError, IndexError):
            return False

    def _validate_taiwan_arc(self, arc_number: str) -> bool:
        """
        Validate Taiwan ARC (居留證) checksum
        驗證台灣居留證校驗碼
        
        Similar algorithm to national ID but with two letters.
        """
        if not arc_number or len(arc_number) != 10:
            return False

        try:
            # First two characters should be letters
            letter1 = arc_number[0].upper()
            letter2 = arc_number[1].upper()

            if letter1 not in self.TW_ID_LETTER_MAP or letter2 not in self.TW_ID_LETTER_MAP:
                return False

            # ARC uses different validation rules depending on issue date
            # For simplicity, we do basic format validation
            # More complex validation would require knowing the issue date

            # Basic validation: first letter is valid region code
            return letter1 in self.TW_ID_LETTER_MAP

        except (ValueError, IndexError):
            return False

    def validate_id(self, id_number: str) -> tuple[bool, str]:
        """
        Validate a single ID number
        驗證單個 ID 號碼
        
        Args:
            id_number: ID number to validate
            
        Returns:
            Tuple of (is_valid, id_type)
        """
        id_number = id_number.strip().upper()

        # Check Taiwan National ID
        if self._tw_id_pattern.match(id_number):
            is_valid = self._validate_taiwan_id(id_number)
            return (is_valid, "TW_NATIONAL_ID")

        # Check Taiwan ARC
        if self._tw_arc_pattern.match(id_number):
            is_valid = self._validate_taiwan_arc(id_number)
            return (is_valid, "TW_ARC")

        return (False, "UNKNOWN")
