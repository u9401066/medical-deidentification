"""
PHI Identification Chain | PHI 識別鏈

Chain for identifying PHI entities in medical text using regulation context.
使用法規上下文在醫療文本中識別 PHI 實體的鏈。

職責 Responsibilities:
- Identify PHI entities in medical text
- Use regulation context for accurate identification
- Support structured output (Pydantic models)
- Coordinate MapReduce processing for long texts
- 在醫療文本中識別 PHI 實體
- 使用法規上下文進行精確識別
- 支援結構化輸出（Pydantic 模型）
- 協調 MapReduce 處理長文本

For Agent-based approach with tool-calling, see:
- phi_agent.py: PHIIdentificationAgent (LLM decides when to use tools)

NOT responsible for:
- Storing or managing regulation documents (use RegulationRetrievalChain)
- Persisting medical text (uses MedicalTextRetriever for ephemeral processing)
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from ..llm.factory import create_llm
from ...domain import PHIEntity
from .regulation_retrieval_chain import RegulationRetrievalChain
from .text_splitter import MedicalTextSplitter
from .embeddings import EmbeddingsManager

# Import PHI identification models from domain layer
from ...domain.phi_identification_models import (
    PHIIdentificationConfig,
)

# Import modularized chain components
from .chains.utils import get_minimal_context
from .chains.map_reduce import identify_phi_with_map_reduce
from .chains.processors import identify_phi_direct


class PHIIdentificationChain:
    """
    Chain for identifying PHI in medical text
    
    職責：從醫療文本中識別需要 mask 的 PHI 實體
    
    Uses:
    - RegulationRetrievalChain for regulation context
    - LLM for structured PHI identification
    - Centralized prompts module
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     PHIIdentificationChain,
        ...     RegulationRetrievalChain,
        ...     RegulationVectorStore,
        ...     EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> reg_chain = RegulationRetrievalChain(store)
        >>> phi_chain = PHIIdentificationChain(reg_chain)
        >>> 
        >>> # Identify PHI
        >>> medical_text = "患者張三，94歲，患有法布瑞氏症..."
        >>> result = phi_chain.identify_phi(medical_text, language="zh-TW")
        >>> 
        >>> # Get PHI entities
        >>> entities = result["entities"]  # List[PHIEntity]
    """
    
    def __init__(
        self,
        regulation_chain: Optional[RegulationRetrievalChain] = None,
        config: Optional[PHIIdentificationConfig] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        max_text_length: int = 2000,  # 超過此長度則分段處理
    ):
        """
        Initialize PHI identification chain
        
        Args:
            regulation_chain: RegulationRetrievalChain for retrieving regulation context
                             (Optional when retrieve_regulation_context=False)
            config: Chain configuration
            chunk_size: Text chunk size for MapReduce splitting (default: 500)
            chunk_overlap: Overlap between chunks (default: 50)
            max_text_length: Maximum text length before chunking (default: 2000)
            
        Note:
            For tool-calling agent approach, use PHIIdentificationAgent instead.
            該 Chain 使用純 LLM 方式，如需工具呼叫請改用 PHIIdentificationAgent。
        """
        self.regulation_chain = regulation_chain
        self.config = config or PHIIdentificationConfig()
        self.max_text_length = max_text_length
        
        # Validate: if retrieve_regulation_context=True, regulation_chain must be provided
        if self.config.retrieve_regulation_context and regulation_chain is None:
            raise ValueError(
                "regulation_chain is required when retrieve_regulation_context=True"
            )
        
        # Initialize LLM
        self.llm = create_llm(self.config.llm_config)
        
        # Initialize MedicalTextSplitter for MapReduce chunking
        self.text_splitter = MedicalTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Get LLM info for logging (handle dict or object)
        if isinstance(self.config.llm_config, dict):
            provider = self.config.llm_config.get("provider", "unknown")
            model_name = self.config.llm_config.get("model_name", "unknown")
        else:
            provider = self.config.llm_config.provider
            model_name = self.config.llm_config.model_name
        
        logger.info(
            f"PHIIdentificationChain initialized with "
            f"LLM: {provider}/{model_name}, "
            f"max_text_length: {max_text_length}"
        )
    
    def identify_phi(
        self,
        text: str,
        language: Optional[str] = None,
        return_source: bool = False,
        return_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Identify PHI in medical text
        
        Uses chunking strategy for long texts to avoid LLM context limits:
        - Text <= max_text_length: Process directly
        - Text > max_text_length: Use MapReduce pattern
        
        使用分段策略處理長文本以避免 LLM 上下文限制：
        - 文本 <= max_text_length：直接處理
        - 文本 > max_text_length：使用 MapReduce 模式
        
        Args:
            text: Medical text to analyze
            language: Language code (e.g., "zh-TW", "en")
            return_source: Whether to return source regulation documents
            return_entities: Whether to return identified entities
            
        Returns:
            Dictionary with:
            - text: Original text
            - language: Detected/provided language
            - total_entities: Count of entities
            - has_phi: Whether PHI was found
            - entities: List[PHIEntity] (if return_entities=True)
            - source_documents: Regulation docs used (if return_source=True)
        """
        logger.info(f"Identifying PHI in text ({len(text)} chars)")
        
        # Check if text needs chunking
        if len(text) > self.max_text_length:
            logger.info(
                f"Text length ({len(text)}) > max_text_length ({self.max_text_length}), "
                f"using MapReduce pattern"
            )
            return self._identify_phi_chunked(text, language, return_source, return_entities)
        else:
            return self._identify_phi_direct(text, language, return_source, return_entities)
    
    def _identify_phi_direct(
        self,
        text: str,
        language: Optional[str] = None,
        return_source: bool = False,
        return_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Direct PHI identification for short texts
        Delegates to chains.processors.identify_phi_direct
        
        Note:
            This is a pure LLM approach without tool pre-scanning.
            For tool-calling agent approach, use PHIIdentificationAgent.
        """
        return identify_phi_direct(
            text=text,
            language=language,
            regulation_chain=self.regulation_chain,
            llm=self.llm,
            config=self.config,
            get_minimal_context_func=lambda: get_minimal_context(self.config.retrieve_regulation_context),
            return_source=return_source,
            return_entities=return_entities,
        )
    
    def _identify_phi_chunked(
        self,
        text: str,
        language: Optional[str] = None,
        return_source: bool = False,
        return_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Chunked PHI identification for long texts using MapReduce
        Delegates to chains.map_reduce.identify_phi_with_map_reduce
        """
        # Use MapReduce pattern
        entities = identify_phi_with_map_reduce(
            text=text,
            llm=self.llm,
            text_splitter=self.text_splitter,
            language=language
        )
        
        # Build response
        result = {
            "text": text,
            "language": language or "unknown",
            "total_entities": len(entities),
            "has_phi": len(entities) > 0
        }
        
        if return_entities:
            result["entities"] = entities
        
        if return_source:
            result["source_documents"] = []  # MapReduce doesn't use regulation docs
        
        return result
