"""
Masking Utilities
遮蔽工具模組

Provides utilities for applying masking strategies to PHI entities.
提供將遮蔽策略應用於 PHI 實體的工具。
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from ....domain import PHIEntity, PHIType, StrategyType
from ..strategies import (
    MaskingStrategy,
    create_masking_strategy
)


class MaskingProcessor:
    """
    Masking processor
    遮蔽處理器
    
    Applies masking strategies to PHI entities in text.
    將遮蔽策略應用於文本中的 PHI 實體。
    
    Key features:
    - Handles multiple PHI entities in a single text
    - Supports PHI-specific strategies
    - Sorts entities to avoid position offset issues
    - Validates masked output
    
    Examples:
        >>> from core.domain import StrategyType
        >>> 
        >>> processor = MaskingProcessor(
        ...     default_strategy=StrategyType.REDACTION,
        ...     phi_specific_strategies={
        ...         PHIType.NAME: StrategyType.PSEUDONYMIZATION
        ...     }
        ... )
        >>> 
        >>> # Apply masking
        >>> masked_text = processor.apply_masking(
        ...     text="Patient John Doe, 94 years old",
        ...     phi_entities=[entity1, entity2]
        ... )
    """
    
    def __init__(
        self,
        default_strategy: StrategyType = StrategyType.REDACTION,
        phi_specific_strategies: Optional[Dict[PHIType, StrategyType]] = None,
        strategy_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize masking processor
        
        Args:
            default_strategy: Default masking strategy
            phi_specific_strategies: PHI-type specific strategies
            strategy_config: Strategy configuration
        """
        self.default_strategy = default_strategy
        self.phi_specific_strategies = phi_specific_strategies or {}
        self.strategy_config = strategy_config or {}
    
    def apply_masking(
        self,
        text: str,
        phi_entities: List[PHIEntity]
    ) -> str:
        """
        Apply masking to text
        
        Args:
            text: Original text
            phi_entities: PHI entities to mask
            
        Returns:
            Masked text
        """
        if not phi_entities:
            logger.debug("No PHI entities to mask")
            return text
        
        logger.info(f"Applying masking to {len(phi_entities)} PHI entities")
        
        # Sort entities by position (descending) to avoid offset issues
        # Process from end to start so positions remain valid
        sorted_entities = sorted(
            phi_entities,
            key=lambda e: e.start_pos,
            reverse=True
        )
        
        masked_text = text
        
        for entity in sorted_entities:
            try:
                # Get masking strategy for this PHI type
                strategy_type = self.phi_specific_strategies.get(
                    entity.type,
                    self.default_strategy
                )
                
                strategy = create_masking_strategy(
                    strategy_type,
                    self.strategy_config
                )
                
                # Mask entity
                masked_value = strategy.mask(entity)
                
                # Replace in text
                masked_text = (
                    masked_text[:entity.start_pos] +
                    masked_value +
                    masked_text[entity.end_pos:]
                )
                
                logger.debug(
                    f"Masked {entity.type.value}: "
                    f"'{entity.text}' -> '{masked_value}'"
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to mask entity {entity.type.value} "
                    f"at position {entity.start_pos}: {e}"
                )
                # Continue with other entities
                continue
        
        logger.success("Masking completed")
        return masked_text
    
    def get_strategy_for_phi(self, phi_type: PHIType) -> MaskingStrategy:
        """
        Get masking strategy for specific PHI type
        
        Args:
            phi_type: PHI type
            
        Returns:
            Masking strategy
        """
        strategy_type = self.phi_specific_strategies.get(
            phi_type,
            self.default_strategy
        )
        
        return create_masking_strategy(
            strategy_type,
            self.strategy_config
        )
    
    def validate_masking(
        self,
        original_text: str,
        masked_text: str,
        phi_entities: List[PHIEntity]
    ) -> bool:
        """
        Validate that PHI entities were properly masked
        
        Args:
            original_text: Original text
            masked_text: Masked text
            phi_entities: PHI entities that should be masked
            
        Returns:
            True if all PHI entities are masked
        """
        for entity in phi_entities:
            # Check if original PHI text still exists in masked text
            if entity.text in masked_text:
                logger.warning(
                    f"PHI entity '{entity.text}' "
                    f"({entity.type.value}) still present in masked text"
                )
                return False
        
        return True


__all__ = [
    "MaskingProcessor",
]
