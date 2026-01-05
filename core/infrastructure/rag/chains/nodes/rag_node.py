"""
RAG Node | RAG 節點

Retrieves regulation context from vector store.
Can be enabled/disabled via configuration.

從向量存儲檢索法規上下文。
可透過配置啟用/禁用。
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger

from .base_node import BaseNode, NodeConfig


@dataclass
class RAGNodeConfig(NodeConfig):
    """RAG Node specific configuration"""
    enabled: bool = True  # RAG on/off switch
    k: int = 3  # Number of documents to retrieve
    score_threshold: float = 0.5  # Minimum relevance score
    include_metadata: bool = True


class RAGNode(BaseNode[dict[str, Any]]):
    """
    RAG Node for regulation context retrieval
    用於法規上下文檢索的 RAG 節點
    
    This node:
    1. Takes medical text as input
    2. Queries regulation vector store
    3. Returns relevant regulation context
    
    Can be disabled when:
    - Using minimal/static context
    - Testing without RAG
    - Performance optimization
    """

    def __init__(
        self,
        regulation_chain=None,  # RegulationRetrievalChain
        config: RAGNodeConfig | None = None,
        **kwargs
    ):
        """
        Initialize RAG node
        
        Args:
            regulation_chain: Regulation retrieval chain (optional if disabled)
            config: RAG node configuration
        """
        super().__init__(config=config or RAGNodeConfig(), **kwargs)
        self.regulation_chain = regulation_chain
        self.rag_config = config or RAGNodeConfig()

    def get_name(self) -> str:
        return "rag_node"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve regulation context
        檢索法規上下文
        
        Args:
            input_data: Must contain 'text' key with medical text
            
        Returns:
            Dict with 'context' and 'source_documents' added
        """
        # Check if RAG is enabled
        if not self.rag_config.enabled:
            logger.debug(f"{self.get_name()}: RAG disabled, using minimal context")
            return {
                **input_data,
                "context": self._get_minimal_context(),
                "source_documents": [],
                "rag_enabled": False,
            }

        # Check if regulation_chain is available
        if self.regulation_chain is None:
            logger.warning(f"{self.get_name()}: No regulation_chain provided, using minimal context")
            return {
                **input_data,
                "context": self._get_minimal_context(),
                "source_documents": [],
                "rag_enabled": False,
            }

        # Get text for query
        text = input_data.get("text", "")
        language = input_data.get("language")

        if not text:
            logger.warning(f"{self.get_name()}: Empty text, returning minimal context")
            return {
                **input_data,
                "context": self._get_minimal_context(),
                "source_documents": [],
                "rag_enabled": False,
            }

        # Build query context (use first 500 chars)
        query_context = text[:500]
        if language:
            query_context = f"[Language: {language}]\n\n{query_context}"

        try:
            # Retrieve regulation documents
            docs = self.regulation_chain.retrieve_by_context(
                medical_context=query_context,
                k=self.rag_config.k
            )

            # Filter by score threshold if available
            if self.rag_config.score_threshold > 0:
                docs = [
                    doc for doc in docs
                    if doc.metadata.get("score", 1.0) >= self.rag_config.score_threshold
                ]

            # Build context string
            context_parts = []
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                if self.rag_config.include_metadata:
                    context_parts.append(f"[{source}]\n{doc.page_content}")
                else:
                    context_parts.append(doc.page_content)

            context = "\n\n".join(context_parts) if context_parts else self._get_minimal_context()

            logger.debug(f"{self.get_name()}: Retrieved {len(docs)} regulation documents")

            return {
                **input_data,
                "context": context,
                "source_documents": docs,
                "rag_enabled": True,
            }

        except Exception as e:
            logger.error(f"{self.get_name()}: RAG retrieval failed: {e}")
            return {
                **input_data,
                "context": self._get_minimal_context(),
                "source_documents": [],
                "rag_enabled": False,
                "rag_error": str(e),
            }

    def _get_minimal_context(self) -> str:
        """Return minimal HIPAA context when RAG is disabled"""
        return """PHI (Protected Health Information) includes:
- Names, dates (except year), phone numbers, fax numbers
- Email addresses, Social Security numbers, medical record numbers
- Health plan beneficiary numbers, account numbers, certificate/license numbers
- Vehicle identifiers, device identifiers, URLs, IP addresses
- Biometric identifiers, photos, and any other unique identifying number

For ages over 89, aggregate into 90+ category.
Geographic subdivisions smaller than state must be de-identified.
"""

    def is_enabled(self) -> bool:
        """Check if RAG is enabled"""
        return self.rag_config.enabled and self.regulation_chain is not None

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable RAG at runtime"""
        self.rag_config.enabled = enabled
        logger.info(f"{self.get_name()}: RAG {'enabled' if enabled else 'disabled'}")
