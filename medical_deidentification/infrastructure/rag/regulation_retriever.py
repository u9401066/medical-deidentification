"""
Regulation Retriever
法規檢索器

Specialized retriever for persistent regulation documents with MMR support.
專門用於持久化法規文件的檢索器，支援 MMR（最大邊際相關性）。
"""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from loguru import logger

from ...domain import RegulationRetrieverConfig
from .regulation_store import RegulationVectorStore


class RegulationRetriever:
    """
    Advanced retriever for regulation documents (persistent)
    
    用於法規文件的高級檢索器（持久化存儲）
    
    Features:
    - MMR search: Balances relevance and diversity
    - PHI-type specific retrieval
    - Multi-PHI type combination (union/intersection)
    - Score-based filtering
    
    特性：
    - MMR 搜索：平衡相關性與多樣性
    - PHI 類型專屬檢索
    - 多 PHI 類型組合（聯集/交集）
    - 基於分數的過濾
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     RegulationVectorStore, RegulationRetriever, EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> retriever = RegulationRetriever(store)
        >>> 
        >>> # Basic retrieval
        >>> docs = retriever.retrieve("patient age over 90 years")
        >>> 
        >>> # With MMR for diversity
        >>> config = RegulationRetrieverConfig(
        ...     search_type="mmr", 
        ...     k=3, 
        ...     lambda_mult=0.7
        ... )
        >>> retriever = RegulationRetriever(store, config)
        >>> docs = retriever.retrieve("genetic information and rare diseases")
        >>> 
        >>> # Retrieve by PHI type
        >>> docs = retriever.retrieve_by_phi_type("AGE_OVER_89")
        >>> 
        >>> # Multi-PHI retrieval
        >>> docs = retriever.retrieve_multi_phi(
        ...     ["AGE_OVER_89", "RARE_DISEASE", "NAME"],
        ...     combine_strategy="union"
        ... )
    """
    
    def __init__(
        self,
        vector_store: RegulationVectorStore,
        config: Optional[RegulationRetrieverConfig] = None
    ):
        """
        Initialize regulation retriever
        
        Args:
            vector_store: RegulationVectorStore instance (persistent)
            config: Retriever configuration. Uses defaults if None.
        """
        self.vector_store = vector_store
        self.config = config or RegulationRetrieverConfig()
        
        # Setup base retriever
        self._setup_retriever()
    
    def _setup_retriever(self) -> None:
        """Setup retriever based on configuration"""
        if self.config.search_type == "mmr":
            self.base_retriever = self.vector_store.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.k,
                    "fetch_k": self.config.fetch_k,
                    "lambda_mult": self.config.lambda_mult,
                }
            )
            logger.debug(
                f"RegulationRetriever setup: MMR "
                f"(k={self.config.k}, lambda={self.config.lambda_mult})"
            )
        else:  # similarity
            search_kwargs: Dict[str, Any] = {"k": self.config.k}
            if self.config.score_threshold is not None:
                search_kwargs["score_threshold"] = self.config.score_threshold
            
            self.base_retriever = self.vector_store.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
            logger.debug(f"RegulationRetriever setup: similarity (k={self.config.k})")
    
    def retrieve(self, query: str) -> List[Document]:
        """
        Retrieve relevant regulation documents
        
        Args:
            query: Query text
            
        Returns:
            List of relevant regulation documents
        """
        logger.info(f"[Regulation] Retrieving for: {query[:50]}...")
        
        docs = self.base_retriever.invoke(query)
        
        logger.info(f"[Regulation] Retrieved {len(docs)} documents")
        return docs
    
    def retrieve_with_scores(
        self,
        query: str
    ) -> List[tuple[Document, float]]:
        """
        Retrieve regulation documents with relevance scores
        
        Args:
            query: Query text
            
        Returns:
            List of (document, score) tuples
        """
        logger.info(f"[Regulation] Retrieving with scores: {query[:50]}...")
        
        docs_with_scores = self.vector_store.similarity_search_with_score(
            query=query,
            k=self.config.k
        )
        
        # Apply score threshold if set
        if self.config.score_threshold is not None:
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores
                if score >= self.config.score_threshold
            ]
        
        logger.info(
            f"[Regulation] Retrieved {len(docs_with_scores)} documents with scores"
        )
        return docs_with_scores
    
    def retrieve_by_phi_type(
        self,
        phi_type: str,
        context: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve regulations for specific PHI type
        
        Args:
            phi_type: PHI type (e.g., "AGE_OVER_89", "RARE_DISEASE")
            context: Optional context for better retrieval
            
        Returns:
            Relevant regulation documents
        """
        # Build query from PHI type
        query_parts = [phi_type.replace("_", " ").lower()]
        
        if context:
            query_parts.append(context)
        
        query = " ".join(query_parts)
        
        logger.info(f"[Regulation] Retrieving for PHI type: {phi_type}")
        return self.retrieve(query)
    
    def retrieve_multi_phi(
        self,
        phi_types: List[str],
        combine_strategy: str = "union"
    ) -> List[Document]:
        """
        Retrieve regulations for multiple PHI types
        
        Args:
            phi_types: List of PHI types
            combine_strategy: How to combine results ('union' or 'intersection')
            
        Returns:
            Combined regulation documents
        """
        logger.info(
            f"[Regulation] Multi-PHI retrieval for {len(phi_types)} types "
            f"(strategy: {combine_strategy})"
        )
        
        if combine_strategy == "union":
            # Retrieve for all types and deduplicate
            all_docs = []
            seen_content = set()
            
            for phi_type in phi_types:
                docs = self.retrieve_by_phi_type(phi_type)
                for doc in docs:
                    content_hash = hash(doc.page_content)
                    if content_hash not in seen_content:
                        all_docs.append(doc)
                        seen_content.add(content_hash)
            
            logger.info(f"[Regulation] Union: {len(all_docs)} unique documents")
            return all_docs
        
        else:  # intersection
            # Find documents that appear for all PHI types
            if not phi_types:
                return []
            
            # Get docs for first type
            common_docs = {
                hash(doc.page_content): doc
                for doc in self.retrieve_by_phi_type(phi_types[0])
            }
            
            # Intersect with remaining types
            for phi_type in phi_types[1:]:
                docs = self.retrieve_by_phi_type(phi_type)
                current_hashes = {hash(doc.page_content) for doc in docs}
                common_docs = {
                    h: doc for h, doc in common_docs.items()
                    if h in current_hashes
                }
            
            result = list(common_docs.values())
            logger.info(f"[Regulation] Intersection: {len(result)} common documents")
            return result
    
    def get_config(self) -> Dict[str, Any]:
        """Get current retriever configuration"""
        return self.config.model_dump()
    
    def update_config(self, **kwargs) -> None:
        """
        Update retriever configuration
        
        Args:
            **kwargs: Configuration fields to update
        """
        # Update config
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Recreate retriever with new config
        self._setup_retriever()
        
        logger.info(f"[Regulation] Config updated: {kwargs}")
    
    def __repr__(self) -> str:
        return (
            f"RegulationRetriever("
            f"search_type={self.config.search_type}, "
            f"k={self.config.k}, "
            f"source=persistent)"
        )


def create_regulation_retriever(
    vector_store: RegulationVectorStore,
    search_type: str = "mmr",
    k: int = 5,
    lambda_mult: float = 0.5,
    **kwargs
) -> RegulationRetriever:
    """
    Factory function to create regulation retriever
    
    Args:
        vector_store: RegulationVectorStore instance
        search_type: 'similarity' or 'mmr'
        k: Number of documents to retrieve
        lambda_mult: Diversity factor for MMR
        **kwargs: Additional config parameters
        
    Returns:
        Configured RegulationRetriever
    
    Examples:
        >>> retriever = create_regulation_retriever(
        ...     vector_store=store,
        ...     search_type="mmr",
        ...     k=3,
        ...     lambda_mult=0.7
        ... )
    """
    config = RegulationRetrieverConfig(
        search_type=search_type,
        k=k,
        lambda_mult=lambda_mult,
        **kwargs
    )
    
    return RegulationRetriever(vector_store, config)
