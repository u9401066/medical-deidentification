"""
Regulation Retrieval Chain | 法規檢索鏈

Chain for retrieving PHI definitions and masking strategies from regulation documents.
從法規文件中檢索 PHI 定義和遮蔽策略的鏈。

職責 Responsibilities:
- Retrieve PHI definitions from regulation vector store
- Get masking strategies for specific PHI types
- Search regulations by medical context keywords
- 從法規向量庫檢索 PHI 定義
- 獲取特定 PHI 類型的遮蔽策略
- 根據醫療上下文關鍵字搜索法規

NOT responsible for:
- Identifying PHI entities in medical text (use PHIIdentificationChain)
- Processing medical documents (use MedicalTextRetriever)
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from loguru import logger

from ...domain import PHIType, RegulationRetrievalConfig, RegulationRetrieverConfig
from .regulation_store import RegulationVectorStore
from .regulation_retriever import RegulationRetriever


class RegulationRetrievalChain:
    """
    Chain for retrieving regulations from vector store
    
    職責：從持久化法規向量庫中檢索 PHI 相關法規
    
    Examples:
        >>> from core.infrastructure.rag import (
        ...     RegulationRetrievalChain,
        ...     RegulationVectorStore,
        ...     EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> chain = RegulationRetrievalChain(store)
        >>> 
        >>> # Get PHI definitions
        >>> phi_docs = chain.get_phi_definitions(["NAME", "AGE_OVER_89"])
        >>> 
        >>> # Get masking strategy
        >>> strategy_docs = chain.get_masking_strategies("AGE_OVER_89")
        >>> 
        >>> # Search by medical context
        >>> context_docs = chain.retrieve_by_context(
        ...     "patient over 90 years old with rare disease"
        ... )
    """
    
    def __init__(
        self,
        vector_store: RegulationVectorStore,
        config: Optional[RegulationRetrievalConfig] = None
    ):
        """
        Initialize regulation retrieval chain
        
        Args:
            vector_store: RegulationVectorStore instance (persistent)
            config: Chain configuration
        """
        self.vector_store = vector_store
        self.config = config or RegulationRetrievalConfig()
        
        # Initialize retriever
        self.retriever = RegulationRetriever(
            vector_store=vector_store,
            config=self.config.retriever_config
        )
        
        logger.info(f"RegulationRetrievalChain initialized with {self.vector_store.get_stats().get('total_vectors', 0)} regulation vectors")
    
    def get_phi_definitions(
        self,
        phi_types: List[str],
        combine_strategy: str = "union"
    ) -> List[Document]:
        """
        Retrieve PHI definitions for multiple types
        
        Args:
            phi_types: List of PHI type names (e.g., ["NAME", "AGE_OVER_89"])
            combine_strategy: 'union' or 'intersection'
            
        Returns:
            Relevant regulation documents defining these PHI types
        """
        logger.info(f"Retrieving PHI definitions for {len(phi_types)} types")
        
        docs = self.retriever.retrieve_multi_phi(
            phi_types=phi_types,
            combine_strategy=combine_strategy
        )
        
        logger.debug(f"Retrieved {len(docs)} regulation documents")
        return docs
    
    def get_masking_strategies(
        self,
        phi_type: str,
        k: Optional[int] = None
    ) -> List[Document]:
        """
        Retrieve masking strategies for specific PHI type
        
        Args:
            phi_type: PHI type (e.g., "AGE_OVER_89", "RARE_DISEASE")
            k: Number of documents to retrieve (uses config default if None)
            
        Returns:
            Regulation documents with masking strategies
        """
        logger.info(f"Retrieving masking strategies for {phi_type}")
        
        # Build query
        query = f"masking strategy for {phi_type.replace('_', ' ').lower()}"
        
        # Temporarily update retriever config if k is specified
        if k is not None:
            original_k = self.retriever.config.k
            self.retriever.update_config(k=k)
            docs = self.retriever.retrieve(query)
            self.retriever.update_config(k=original_k)
        else:
            docs = self.retriever.retrieve(query)
        
        logger.debug(f"Retrieved {len(docs)} masking strategy documents")
        return docs
    
    def retrieve_by_context(
        self,
        medical_context: str,
        k: Optional[int] = None,
        filter_by_source: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve regulations based on medical context keywords
        
        Args:
            medical_context: Medical context or keywords (e.g., "patient over 90 with diabetes")
            k: Number of documents to retrieve
            filter_by_source: Filter by regulation source (e.g., "HIPAA", "GDPR")
            
        Returns:
            Relevant regulation documents
        """
        logger.info(f"Retrieving regulations by context: '{medical_context[:50]}...'")
        
        # Update k if specified
        if k is not None:
            original_k = self.retriever.config.k
            self.retriever.update_config(k=k)
            docs = self.retriever.retrieve(medical_context)
            self.retriever.update_config(k=original_k)
        else:
            docs = self.retriever.retrieve(medical_context)
        
        # Filter by source if specified
        if filter_by_source:
            docs = [
                doc for doc in docs
                if filter_by_source.upper() in doc.metadata.get("source", "").upper()
            ]
            logger.debug(f"Filtered to {len(docs)} documents from {filter_by_source}")
        
        return docs
    
    def get_phi_type_details(
        self,
        phi_type: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive details for a specific PHI type
        
        Args:
            phi_type: PHI type (e.g., "AGE_OVER_89")
            
        Returns:
            Dictionary with:
            - definition_docs: Regulation documents defining this PHI type
            - masking_docs: Documents with masking strategies
            - examples: Example texts from regulations
        """
        logger.info(f"Getting comprehensive details for {phi_type}")
        
        # Get definitions
        definition_docs = self.get_phi_definitions([phi_type])
        
        # Get masking strategies
        masking_docs = self.get_masking_strategies(phi_type)
        
        # Extract examples from documents
        examples = []
        for doc in definition_docs:
            # Look for example patterns in content
            if "example" in doc.page_content.lower():
                examples.append(doc.page_content)
        
        return {
            "phi_type": phi_type,
            "definition_docs": definition_docs,
            "masking_docs": masking_docs,
            "examples": examples,
            "total_regulations": len(set(definition_docs + masking_docs))
        }
    
    def search_regulation_by_keyword(
        self,
        keyword: str,
        exact_match: bool = False
    ) -> List[Document]:
        """
        Search regulations by specific keyword
        
        Args:
            keyword: Keyword to search (e.g., "rare disease", "over 89")
            exact_match: Whether to require exact phrase match
            
        Returns:
            Matching regulation documents
        """
        logger.info(f"Searching regulations for keyword: '{keyword}'")
        
        docs = self.retriever.retrieve(keyword)
        
        if exact_match:
            # Filter for exact matches
            docs = [
                doc for doc in docs
                if keyword.lower() in doc.page_content.lower()
            ]
            logger.debug(f"Exact match filtered to {len(docs)} documents")
        
        return docs
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        return {
            "vector_store_stats": self.vector_store.get_stats(),
            "retriever_config": self.config.retriever_config.model_dump(),
            "top_k": self.config.top_k
        }
    
    def __repr__(self) -> str:
        return (
            f"RegulationRetrievalChain("
            f"vectors={self.vector_store.get_stats().get('total_vectors', 0)}, "
            f"search_type={self.config.retriever_config.search_type})"
        )


def create_regulation_retrieval_chain(
    vector_store: RegulationVectorStore,
    search_type: str = "mmr",
    top_k: int = 5,
    **kwargs
) -> RegulationRetrievalChain:
    """
    Factory function to create regulation retrieval chain
    
    Args:
        vector_store: RegulationVectorStore instance
        search_type: Retriever search type ('similarity' or 'mmr')
        top_k: Number of documents to retrieve
        **kwargs: Additional config parameters
        
    Returns:
        Configured RegulationRetrievalChain
    
    Examples:
        >>> chain = create_regulation_retrieval_chain(
        ...     vector_store=store,
        ...     search_type="mmr",
        ...     top_k=5
        ... )
    """
    # Create retriever config
    retriever_config = RegulationRetrieverConfig(
        search_type=search_type,
        k=top_k
    )
    
    # Create chain config
    config = RegulationRetrievalConfig(
        retriever_config=retriever_config,
        top_k=top_k,
        **kwargs
    )
    
    return RegulationRetrievalChain(vector_store, config)
