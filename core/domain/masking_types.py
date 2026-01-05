"""
Masking Strategy Types
遮蔽策略類型

Domain-level definitions for masking strategies.
遮蔽策略的領域層定義。

This module contains type definitions for masking strategies,
following DDD principles where types belong in the domain layer.
"""

from enum import Enum


class StrategyType(str, Enum):
    """
    遮蔽策略類型 | Masking strategy types
    
    Defines the available masking strategies for PHI de-identification.
    定義 PHI 去識別化的可用遮蔽策略。
    
    Strategies:
    -----------
    REDACTION: Replace with placeholder (e.g., "[REDACTED]")
        刪除策略：替換為占位符
        
    GENERALIZATION: Replace with broader category (e.g., "94歲" → "≥90歲")
        泛化策略：替換為更廣泛的類別
        
    PSEUDONYMIZATION: Replace with consistent fake value (hash-based)
        假名化策略：替換為一致的假值（基於雜湊）
        
    DATE_SHIFTING: Shift dates by random offset
        日期偏移策略：將日期偏移隨機量
        
    PARTIAL_MASKING: Mask part of the value (e.g., "A12****89")
        部分遮蔽策略：遮蔽值的一部分
        
    SUPPRESSION: Remove entity completely
        抑制策略：完全移除實體
    
    Examples:
    ---------
    >>> strategy = StrategyType.GENERALIZATION
    >>> print(strategy.value)
    'generalization'
    
    >>> # Check if strategy is appropriate for age over 89
    >>> from core.domain import PHIType
    >>> phi_type = PHIType.AGE_OVER_89
    >>> recommended_strategy = StrategyType.GENERALIZATION
    """
    
    REDACTION = "redaction"
    GENERALIZATION = "generalization"
    PSEUDONYMIZATION = "pseudonymization"
    DATE_SHIFTING = "date_shifting"
    PARTIAL_MASKING = "partial_masking"
    SUPPRESSION = "suppression"


__all__ = [
    "StrategyType",
]
