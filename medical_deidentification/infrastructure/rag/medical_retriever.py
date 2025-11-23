"""
Medical Text Retriever
醫療文本檢索器

Specialized retriever for ephemeral medical documents (in-memory only).
專門用於臨時醫療文件的檢索器（僅記憶體，不持久化）。
"""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from loguru import logger

from ...domain import MedicalRetrieverConfig
from .embeddings import EmbeddingsManager


class MedicalTextRetriever:
    """
    Ephemeral retriever for medical documents (in-memory only)
    
    臨時醫療文本檢索器（僅記憶體，不持久化）
    
    Features:
    - In-memory processing (no persistence)
    - Smaller chunks for medical context
    - Automatic cleanup after use
    - Privacy-preserving design
    
    特性：
    - 記憶體處理（不持久化）
    - 較小的 chunk 適合醫療文本
    - 使用後自動清理
    - 隱私保護設計
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     MedicalTextRetriever, EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> retriever = MedicalTextRetriever(embeddings)
        >>> 
        >>> # Process medical document (ephemeral)
        >>> medical_text = "Patient John Smith, age 92..."
        >>> results = retriever.retrieve_from_text(
        ...     text=medical_text,
        ...     query="What is the patient's age?"
        ... )
        >>> 
        >>> # Results contain relevant chunks
        >>> for doc in results:
        ...     print(doc.page_content)
        >>> 
        >>> # Vector store is automatically destroyed after use
    """
    
    def __init__(
        self,
        embeddings_manager: EmbeddingsManager,
        config: Optional[MedicalRetrieverConfig] = None
    ):
        """
        Initialize medical text retriever
        
        Args:
            embeddings_manager: EmbeddingsManager instance
            config: Retriever configuration. Uses defaults if None.
        """
        self.embeddings_manager = embeddings_manager
        self.config = config or MedicalRetrieverConfig()
        
        logger.debug(
            f"[Medical] Retriever initialized "
            f"(ephemeral, chunk_size={self.config.chunk_size})"
        )
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split medical text into chunks
        
        Args:
            text: Medical document text
            
        Returns:
            List of text chunks
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        chunks = text_splitter.split_text(text)
        logger.debug(f"[Medical] Split into {len(chunks)} chunks")
        return chunks
    
    def _create_temp_vectorstore(self, text: str) -> FAISS:
        """
        Create temporary in-memory vector store
        
        Args:
            text: Medical document text
            
        Returns:
            Ephemeral FAISS vector store
        """
        chunks = self._split_text(text)
        
        vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=self.embeddings_manager.embeddings
        )
        
        logger.debug(
            f"[Medical] Created ephemeral vectorstore "
            f"({len(chunks)} chunks, in-memory only)"
        )
        
        return vectorstore
    
    def retrieve_from_text(
        self,
        text: str,
        query: str,
        k: Optional[int] = None
    ) -> List[Document]:
        """
        Retrieve relevant chunks from medical text (ephemeral)
        
        Args:
            text: Medical document text
            query: Query for retrieval
            k: Number of results (uses config.k if None)
            
        Returns:
            List of relevant document chunks
            
        Note:
            Vector store is created and destroyed within this method.
            Medical text is never persisted to disk.
        """
        k = k or self.config.k
        
        logger.info(
            f"[Medical] Retrieving from text ({len(text)} chars) "
            f"for query: {query[:50]}..."
        )
        
        # Create temporary vectorstore
        temp_store = self._create_temp_vectorstore(text)
        
        try:
            # Retrieve relevant chunks
            if self.config.score_threshold is not None:
                # With score filtering
                docs_with_scores = temp_store.similarity_search_with_score(
                    query, k=k
                )
                docs = [
                    doc for doc, score in docs_with_scores
                    if score >= self.config.score_threshold
                ]
            else:
                # Without score filtering
                docs = temp_store.similarity_search(query, k=k)
            
            logger.info(f"[Medical] Retrieved {len(docs)} relevant chunks")
            return docs
            
        finally:
            # Explicitly destroy temporary store
            del temp_store
            logger.debug("[Medical] Ephemeral vectorstore destroyed")
    
    def retrieve_from_text_with_scores(
        self,
        text: str,
        query: str,
        k: Optional[int] = None
    ) -> List[tuple[Document, float]]:
        """
        Retrieve relevant chunks with scores (ephemeral)
        
        Args:
            text: Medical document text
            query: Query for retrieval
            k: Number of results (uses config.k if None)
            
        Returns:
            List of (document, score) tuples
        """
        k = k or self.config.k
        
        logger.info(
            f"[Medical] Retrieving with scores from text ({len(text)} chars)"
        )
        
        # Create temporary vectorstore
        temp_store = self._create_temp_vectorstore(text)
        
        try:
            # Retrieve with scores
            docs_with_scores = temp_store.similarity_search_with_score(query, k=k)
            
            # Apply score threshold if set
            if self.config.score_threshold is not None:
                docs_with_scores = [
                    (doc, score) for doc, score in docs_with_scores
                    if score >= self.config.score_threshold
                ]
            
            logger.info(
                f"[Medical] Retrieved {len(docs_with_scores)} chunks with scores"
            )
            return docs_with_scores
            
        finally:
            # Explicitly destroy temporary store
            del temp_store
            logger.debug("[Medical] Ephemeral vectorstore destroyed")
    
    def retrieve_multiple_sections(
        self,
        text: str,
        queries: List[str],
        k: Optional[int] = None
    ) -> Dict[str, List[Document]]:
        """
        Retrieve multiple sections from medical text
        
        Args:
            text: Medical document text
            queries: List of queries (e.g., ["age", "diagnosis", "medications"])
            k: Number of results per query
            
        Returns:
            Dictionary mapping query to retrieved documents
        """
        k = k or self.config.k
        
        logger.info(
            f"[Medical] Multi-section retrieval "
            f"({len(queries)} queries, {len(text)} chars)"
        )
        
        # Create temporary vectorstore (reuse for all queries)
        temp_store = self._create_temp_vectorstore(text)
        
        try:
            results = {}
            
            for query in queries:
                docs = temp_store.similarity_search(query, k=k)
                results[query] = docs
                logger.debug(f"[Medical] Query '{query}': {len(docs)} chunks")
            
            logger.info(
                f"[Medical] Multi-section complete: {len(results)} queries processed"
            )
            return results
            
        finally:
            # Explicitly destroy temporary store
            del temp_store
            logger.debug("[Medical] Ephemeral vectorstore destroyed")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current retriever configuration"""
        return self.config.model_dump()
    
    def update_config(self, **kwargs) -> None:
        """
        Update retriever configuration
        
        Args:
            **kwargs: Configuration fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        logger.info(f"[Medical] Config updated: {kwargs}")
    
    def __repr__(self) -> str:
        return (
            f"MedicalTextRetriever("
            f"chunk_size={self.config.chunk_size}, "
            f"k={self.config.k}, "
            f"source=ephemeral)"
        )


def create_medical_retriever(
    embeddings_manager: EmbeddingsManager,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    k: int = 3,
    **kwargs
) -> MedicalTextRetriever:
    """
    Factory function to create medical text retriever
    
    Args:
        embeddings_manager: EmbeddingsManager instance
        chunk_size: Text chunk size
        chunk_overlap: Chunk overlap
        k: Number of results to retrieve
        **kwargs: Additional config parameters
        
    Returns:
        Configured MedicalTextRetriever
    
    Examples:
        >>> retriever = create_medical_retriever(
        ...     embeddings_manager=embeddings,
        ...     chunk_size=500,
        ...     k=3
        ... )
    """
    config = MedicalRetrieverConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        k=k,
        **kwargs
    )
    
    return MedicalTextRetriever(embeddings_manager, config)
