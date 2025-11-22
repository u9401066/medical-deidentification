"""
Regulation Retriever
法規檢索器

Advanced retrieval with MMR (Maximal Marginal Relevance) for diversity.
使用 MMR（最大邊際相關性）的高級檢索，確保結果多樣性。
"""

from typing import List, Optional, Dict, Any
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger

from .regulation_store import RegulationVectorStore


class RetrieverConfig(BaseModel):
    """檢索器配置"""
    
    search_type: str = Field(
        default="mmr",
        description="Search type: 'similarity' or 'mmr'"
    )
    k: int = Field(
        default=5,
        description="Number of documents to retrieve"
    )
    fetch_k: int = Field(
        default=20,
        description="Number of documents to fetch before MMR"
    )
    lambda_mult: float = Field(
        default=0.5,
        description="Diversity factor for MMR (0=max diversity, 1=max relevance)"
    )
    score_threshold: Optional[float] = Field(
        default=None,
        description="Minimum relevance score threshold"
    )
    use_compression: bool = Field(
        default=False,
        description="Use LLM-based compression to filter irrelevant content"
    )


class RegulationRetriever:
    """
    Advanced retriever for regulation documents
    
    Supports multiple search strategies:
    - Similarity search: Pure cosine similarity
    - MMR: Balances relevance and diversity
    - Compression: LLM filters irrelevant content
    
    高級法規檢索器，支援多種搜索策略：
    - 相似度搜索：純餘弦相似度
    - MMR：平衡相關性與多樣性
    - 壓縮：LLM 過濾不相關內容
    
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
        >>> config = RetrieverConfig(search_type="mmr", k=3, lambda_mult=0.7)
        >>> retriever = RegulationRetriever(store, config)
        >>> docs = retriever.retrieve("genetic information and rare diseases")
        >>> 
        >>> # With score threshold
        >>> config = RetrieverConfig(score_threshold=0.7)
        >>> retriever = RegulationRetriever(store, config)
        >>> docs = retriever.retrieve_with_scores("HIPAA identifiers")
    """
    
    def __init__(
        self,
        vector_store: RegulationVectorStore,
        config: Optional[RetrieverConfig] = None
    ):
        """
        Initialize retriever
        
        Args:
            vector_store: RegulationVectorStore instance
            config: Retriever configuration. Uses defaults if None.
        """
        self.vector_store = vector_store
        self.config = config or RetrieverConfig()
        
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
        else:  # similarity
            search_kwargs = {"k": self.config.k}
            if self.config.score_threshold is not None:
                search_kwargs["score_threshold"] = self.config.score_threshold
            
            self.base_retriever = self.vector_store.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
        
        logger.debug(f"Retriever setup: {self.config.search_type}")
    
    def retrieve(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents
        
        Args:
            query: Query text
            
        Returns:
            List of relevant documents
        """
        logger.info(f"Retrieving documents for query: {query[:50]}...")
        
        docs = self.base_retriever.get_relevant_documents(query)
        
        logger.info(f"Retrieved {len(docs)} documents")
        return docs
    
    def retrieve_with_scores(
        self,
        query: str
    ) -> List[tuple[Document, float]]:
        """
        Retrieve documents with relevance scores
        
        Args:
            query: Query text
            
        Returns:
            List of (document, score) tuples
        """
        logger.info(f"Retrieving with scores for query: {query[:50]}...")
        
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
        
        logger.info(f"Retrieved {len(docs_with_scores)} documents with scores")
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
        # Build query
        query_parts = [phi_type.replace("_", " ").lower()]
        
        if context:
            query_parts.append(context)
        
        query = " ".join(query_parts)
        
        logger.info(f"Retrieving regulations for PHI type: {phi_type}")
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
        logger.info(f"Retrieving for {len(phi_types)} PHI types")
        
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
            
            logger.info(f"Union retrieval: {len(all_docs)} unique documents")
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
            logger.info(f"Intersection retrieval: {len(result)} common documents")
            return result
    
    def create_compressed_retriever(
        self,
        llm: Optional[ChatOpenAI] = None
    ) -> ContextualCompressionRetriever:
        """
        Create retriever with LLM-based compression
        
        Compression filters out irrelevant content from retrieved documents,
        keeping only the parts relevant to the query.
        
        Args:
            llm: LLM for compression. Uses default if None.
            
        Returns:
            Compressed retriever
        """
        if llm is None:
            llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        
        compressor = LLMChainExtractor.from_llm(llm)
        
        compressed_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=self.base_retriever
        )
        
        logger.info("Created compressed retriever with LLM filter")
        return compressed_retriever
    
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
        
        logger.info(f"Updated retriever config: {kwargs}")
    
    def __repr__(self) -> str:
        return (
            f"RegulationRetriever("
            f"search_type={self.config.search_type}, "
            f"k={self.config.k})"
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
    config = RetrieverConfig(
        search_type=search_type,
        k=k,
        lambda_mult=lambda_mult,
        **kwargs
    )
    
    return RegulationRetriever(vector_store, config)
