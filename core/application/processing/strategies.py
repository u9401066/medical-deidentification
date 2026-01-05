"""
Masking Strategies
遮蔽策略

Implements various strategies for masking identified PHI.
實作各種 PHI 遮蔽策略。

Strategies:
- Redaction: Replace with placeholder (e.g., "[REDACTED]")
- Generalization: Replace with broader category (e.g., "94歲" → "≥90歲")
- Pseudonymization: Replace with consistent fake value
- Date Shifting: Shift dates by random offset
- Partial Masking: Mask part of the value (e.g., "A12****89")
"""

import hashlib
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from ...domain import PHIEntity, PHIType, StrategyType


class MaskingStrategy(ABC):
    """
    Abstract base class for masking strategies
    遮蔽策略抽象基類
    
    All masking strategies must implement the mask() method.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration
        """
        self.config = config or {}

    @abstractmethod
    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """
        Mask PHI entity
        
        Args:
            entity: PHI entity to mask
            context: Additional context for masking
            
        Returns:
            Masked value
        """
        pass

    @abstractmethod
    def get_strategy_type(self) -> StrategyType:
        """Get strategy type"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"


class RedactionStrategy(MaskingStrategy):
    """
    Redaction strategy: Replace with placeholder
    刪除策略：替換為占位符
    
    Examples:
        >>> strategy = RedactionStrategy(config={"placeholder": "[REDACTED]"})
        >>> masked = strategy.mask(entity)
        "[REDACTED]"
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize redaction strategy
        
        Config options:
            - placeholder: Placeholder text (default: "[REDACTED]")
            - preserve_length: Whether to preserve text length (default: False)
            - mask_char: Character for length preservation (default: "*")
        """
        super().__init__(config)
        self.placeholder = self.config.get("placeholder", "[REDACTED]")
        self.preserve_length = self.config.get("preserve_length", False)
        self.mask_char = self.config.get("mask_char", "*")

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Mask with placeholder or asterisks"""
        if self.preserve_length:
            return self.mask_char * len(entity.text)
        return self.placeholder

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.REDACTION


class GeneralizationStrategy(MaskingStrategy):
    """
    Generalization strategy: Replace with broader category
    泛化策略：替換為更廣泛的類別
    
    Examples:
        >>> strategy = GeneralizationStrategy()
        >>> # Age over 89 → "≥90歲"
        >>> masked = strategy.mask(entity)
    """

    # Generalization rules
    _GENERALIZATION_RULES = {
        PHIType.AGE_OVER_89: lambda age: "≥90 years" if "year" in age.lower() else "≥90歲",
        PHIType.AGE_OVER_90: lambda age: ">90 years" if "year" in age.lower() else ">90歲",
        PHIType.DATE: lambda date: date[:4] if len(date) >= 4 else "[DATE]",  # Keep year only
        PHIType.LOCATION: lambda loc: "[地區]" if any(c >= '\u4e00' and c <= '\u9fff' for c in loc) else "[LOCATION]",
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize generalization strategy
        
        Config options:
            - custom_rules: Custom generalization rules (dict)
        """
        super().__init__(config)
        self.custom_rules = self.config.get("custom_rules", {})

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Generalize to broader category"""
        phi_type = entity.type  # Fixed: use entity.type not entity.phi_type

        # Check custom rules first
        if phi_type in self.custom_rules:
            rule = self.custom_rules[phi_type]
            return rule(entity.text)

        # Check built-in rules
        if phi_type in self._GENERALIZATION_RULES:
            rule = self._GENERALIZATION_RULES[phi_type]
            return rule(entity.text)

        # Default: use redaction
        logger.warning(f"No generalization rule for {phi_type}, using redaction")
        return "[GENERALIZED]"

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.GENERALIZATION


class PseudonymizationStrategy(MaskingStrategy):
    """
    Pseudonymization strategy: Replace with consistent fake value
    假名化策略：替換為一致的假值
    
    Uses hash-based approach to ensure consistency within document.
    
    Examples:
        >>> strategy = PseudonymizationStrategy()
        >>> masked1 = strategy.mask(entity1)  # "張三" → "Patient-A7F8"
        >>> masked2 = strategy.mask(entity1)  # "張三" → "Patient-A7F8" (same)
    """

    # Pseudonym templates (using existing PHIType values only)
    _TEMPLATES = {
        PHIType.NAME: "Patient-{hash}",
        PHIType.PHONE: "XXX-XXXX-{hash}",
        PHIType.EMAIL: "patient{hash}@example.com",
        PHIType.MEDICAL_RECORD_NUMBER: "MRN-{hash}",
        PHIType.SSN: "XXX-XX-{hash}",
        PHIType.ID: "ID-{hash}",
        PHIType.ACCOUNT_NUMBER: "ACC-{hash}",
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize pseudonymization strategy
        
        Config options:
            - salt: Salt for hashing (for consistency)
            - hash_length: Length of hash suffix (default: 4)
            - custom_templates: Custom pseudonym templates
        """
        super().__init__(config)
        self.salt = self.config.get("salt", "default-salt")
        self.hash_length = self.config.get("hash_length", 4)
        self.custom_templates = self.config.get("custom_templates", {})

        # Cache for consistency
        self._pseudonym_cache: dict[str, str] = {}

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Generate consistent pseudonym"""
        # Check cache
        cache_key = f"{entity.type}:{entity.text}"  # Fixed: use entity.type
        if cache_key in self._pseudonym_cache:
            return self._pseudonym_cache[cache_key]

        # Generate hash
        hash_value = self._generate_hash(entity.text)

        # Get template
        phi_type = entity.type  # Fixed: use entity.type
        if phi_type in self.custom_templates:
            template = self.custom_templates[phi_type]
        elif phi_type in self._TEMPLATES:
            template = self._TEMPLATES[phi_type]
        else:
            template = "PSEUDO-{hash}"

        # Generate pseudonym
        pseudonym = template.format(hash=hash_value)

        # Cache and return
        self._pseudonym_cache[cache_key] = pseudonym
        return pseudonym

    def _generate_hash(self, text: str) -> str:
        """Generate short hash"""
        full_hash = hashlib.sha256(f"{self.salt}{text}".encode()).hexdigest()
        return full_hash[:self.hash_length].upper()

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.PSEUDONYMIZATION


class DateShiftingStrategy(MaskingStrategy):
    """
    Date shifting strategy: Shift dates by random offset
    日期偏移策略：將日期偏移隨機量
    
    Maintains temporal relationships within document.
    
    Examples:
        >>> strategy = DateShiftingStrategy(config={"offset_days": 30})
        >>> masked = strategy.mask(entity)  # "2024-01-15" → "2024-02-14"
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize date shifting strategy
        
        Config options:
            - offset_days: Fixed offset in days (default: None = random)
            - offset_range: Random offset range (default: [-365, 365])
            - preserve_year: Keep year unchanged (default: False)
            - seed: Random seed for consistency (default: None)
        """
        super().__init__(config)
        self.offset_days = self.config.get("offset_days")
        self.offset_range = self.config.get("offset_range", [-365, 365])
        self.preserve_year = self.config.get("preserve_year", False)

        # Set random seed for consistency
        seed = self.config.get("seed")
        if seed is not None:
            random.seed(seed)

        # Cache offset for consistency within document
        self._offset = None

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Shift date"""
        date_text = entity.text

        try:
            # Try to parse date
            date_obj = self._parse_date(date_text)

            # Get or generate offset
            if self._offset is None:
                if self.offset_days is not None:
                    self._offset = self.offset_days
                else:
                    self._offset = random.randint(*self.offset_range)

            # Apply offset
            shifted_date = date_obj + timedelta(days=self._offset)

            # Preserve year if configured
            if self.preserve_year:
                shifted_date = shifted_date.replace(year=date_obj.year)

            # Format back to string
            return shifted_date.strftime("%Y-%m-%d")

        except Exception as e:
            logger.warning(f"Failed to shift date '{date_text}': {e}")
            return "[DATE]"

    def _parse_date(self, date_text: str) -> datetime:
        """Parse date from text"""
        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_text}")

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.DATE_SHIFTING


class PartialMaskingStrategy(MaskingStrategy):
    """
    Partial masking strategy: Mask part of the value
    部分遮蔽策略：遮蔽值的一部分
    
    Examples:
        >>> strategy = PartialMaskingStrategy(config={"keep_prefix": 2, "keep_suffix": 2})
        >>> masked = strategy.mask(entity)  # "A123456789" → "A1******89"
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize partial masking strategy
        
        Config options:
            - keep_prefix: Number of characters to keep at start (default: 2)
            - keep_suffix: Number of characters to keep at end (default: 2)
            - mask_char: Character for masking (default: "*")
        """
        super().__init__(config)
        self.keep_prefix = self.config.get("keep_prefix", 2)
        self.keep_suffix = self.config.get("keep_suffix", 2)
        self.mask_char = self.config.get("mask_char", "*")

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Partially mask value"""
        text = entity.text
        text_len = len(text)

        # If too short, fully mask
        if text_len <= self.keep_prefix + self.keep_suffix:
            return self.mask_char * text_len

        # Partial mask
        prefix = text[:self.keep_prefix]
        suffix = text[-self.keep_suffix:]
        middle_len = text_len - self.keep_prefix - self.keep_suffix

        return f"{prefix}{self.mask_char * middle_len}{suffix}"

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.PARTIAL_MASKING


class SuppressionStrategy(MaskingStrategy):
    """
    Suppression strategy: Remove entity completely
    抑制策略：完全移除實體
    
    Examples:
        >>> strategy = SuppressionStrategy()
        >>> masked = strategy.mask(entity)  # Returns empty string
    """

    def mask(self, entity: PHIEntity, context: dict[str, Any] | None = None) -> str:
        """Suppress by returning empty string"""
        return ""

    def get_strategy_type(self) -> StrategyType:
        return StrategyType.SUPPRESSION


# Strategy registry
_STRATEGY_REGISTRY: dict[StrategyType, type] = {
    StrategyType.REDACTION: RedactionStrategy,
    StrategyType.GENERALIZATION: GeneralizationStrategy,
    StrategyType.PSEUDONYMIZATION: PseudonymizationStrategy,
    StrategyType.DATE_SHIFTING: DateShiftingStrategy,
    StrategyType.PARTIAL_MASKING: PartialMaskingStrategy,
    StrategyType.SUPPRESSION: SuppressionStrategy,
}


def create_masking_strategy(
    strategy_type: StrategyType,
    config: dict[str, Any] | None = None
) -> MaskingStrategy:
    """
    Factory function to create masking strategy
    
    Args:
        strategy_type: Type of strategy
        config: Strategy configuration
        
    Returns:
        MaskingStrategy instance
    
    Examples:
        >>> strategy = create_masking_strategy(
        ...     StrategyType.GENERALIZATION,
        ...     config={"custom_rules": {...}}
        ... )
    """
    if strategy_type not in _STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    strategy_class = _STRATEGY_REGISTRY[strategy_type]
    return strategy_class(config)


def get_default_strategy_for_phi_type(phi_type: PHIType) -> StrategyType:
    """
    Get default masking strategy for PHI type
    
    Args:
        phi_type: PHI type
        
    Returns:
        Recommended strategy type
    """
    # Age over 89/90 → Generalization
    if phi_type in [PHIType.AGE_OVER_89, PHIType.AGE_OVER_90]:
        return StrategyType.GENERALIZATION

    # Names, MRN → Pseudonymization
    if phi_type in [PHIType.NAME, PHIType.MEDICAL_RECORD_NUMBER]:
        return StrategyType.PSEUDONYMIZATION

    # Dates → Date shifting
    if phi_type == PHIType.DATE:
        return StrategyType.DATE_SHIFTING

    # Phone, SSN, ID → Partial masking
    if phi_type in [PHIType.PHONE, PHIType.SSN, PHIType.ID, PHIType.MEDICAL_RECORD_NUMBER]:
        return StrategyType.PARTIAL_MASKING

    # Default → Redaction
    return StrategyType.REDACTION
