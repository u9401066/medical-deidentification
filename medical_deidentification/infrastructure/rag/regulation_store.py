"""
Regulation Vector Store
法規向量資料庫

Persistent vector storage for regulation documents using FAISS.
使用 FAISS 的法規文件持久化向量存儲。

Privacy Design:
- Regulation documents (public info) are persisted
- Medical documents are processed in-memory only (ephemeral)
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pydantic import BaseModel, Field
from loguru import logger

from .embeddings import EmbeddingsManager


class RegulationStoreConfig(BaseModel):
    """法規向量庫配置"""
    
    source_dir: Path = Field(
        default=Path("regulations/source_documents"),
        description="Directory containing regulation source documents"
    )
    vectorstore_dir: Path = Field(
        default=Path("regulations/vectorstore"),
        description="Directory for persistent vector store"
    )
    chunk_size: int = Field(
        default=1000,
        description="Text chunk size for splitting documents"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )
    file_patterns: List[str] = Field(
        default_factory=lambda: ["**/*.md", "**/*.txt"],
        description="File patterns to load"
    )


class RegulationVectorStore:
    """
    Persistent vector store for regulation documents
    
    Manages loading, chunking, embedding, and persisting regulation documents
    for semantic search in the de-identification RAG system.
    
    管理法規文件的載入、分塊、嵌入和持久化，用於去識別化 RAG 系統的語義搜索。
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     RegulationVectorStore, EmbeddingsManager
        ... )
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore(embeddings_manager=embeddings)
        >>> 
        >>> # Build vector store from source documents
        >>> store.build_from_source()
        >>> 
        >>> # Or load existing vector store
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> 
        >>> # Search for relevant regulations
        >>> results = store.similarity_search("age over 89 years old", k=3)
    """
    
    def __init__(
        self,
        embeddings_manager: EmbeddingsManager,
        config: Optional[RegulationStoreConfig] = None
    ):
        """
        Initialize regulation vector store
        
        Args:
            embeddings_manager: EmbeddingsManager instance
            config: Store configuration. Uses defaults if None.
        """
        self.embeddings_manager = embeddings_manager
        self.config = config or RegulationStoreConfig()
        self._vectorstore: Optional[FAISS] = None
        
        # Ensure directories exist
        self.config.source_dir.mkdir(parents=True, exist_ok=True)
        self.config.vectorstore_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def vectorstore(self) -> FAISS:
        """Get vector store (loads if not already loaded)"""
        if self._vectorstore is None:
            raise RuntimeError(
                "Vector store not initialized. Call build_from_source() or load()."
            )
        return self._vectorstore
    
    def load_documents(self) -> List[Document]:
        """
        Load regulation documents from source directory
        
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"Loading documents from {self.config.source_dir}")
        
        documents = []
        
        # Load markdown files
        md_loader = DirectoryLoader(
            str(self.config.source_dir),
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True
        )
        documents.extend(md_loader.load())
        
        # Load text files
        txt_loader = DirectoryLoader(
            str(self.config.source_dir),
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        documents.extend(txt_loader.load())
        
        logger.info(f"Loaded {len(documents)} documents")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of document chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks
    
    def build_from_source(self, force_rebuild: bool = False) -> "RegulationVectorStore":
        """
        Build vector store from source documents
        
        Args:
            force_rebuild: If True, rebuild even if store exists
            
        Returns:
            Self for chaining
        """
        vectorstore_path = self.config.vectorstore_dir / "index.faiss"
        
        # Check if already exists
        if vectorstore_path.exists() and not force_rebuild:
            logger.info("Vector store already exists. Loading...")
            return self.load()
        
        logger.info("Building vector store from source documents...")
        
        # Load and split documents
        documents = self.load_documents()
        if not documents:
            raise ValueError(
                f"No documents found in {self.config.source_dir}. "
                "Please add regulation documents before building store."
            )
        
        chunks = self.split_documents(documents)
        
        # Create vector store
        logger.info("Creating embeddings and building FAISS index...")
        self._vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings_manager.embeddings
        )
        
        # Save to disk
        self.save()
        
        logger.success(
            f"Vector store built successfully with {len(chunks)} chunks"
        )
        return self
    
    def save(self) -> None:
        """Save vector store to disk"""
        if self._vectorstore is None:
            raise RuntimeError("No vector store to save")
        
        logger.info(f"Saving vector store to {self.config.vectorstore_dir}")
        self._vectorstore.save_local(str(self.config.vectorstore_dir))
        logger.success("Vector store saved")
    
    @classmethod
    def load(
        cls,
        embeddings_manager: EmbeddingsManager,
        config: Optional[RegulationStoreConfig] = None
    ) -> "RegulationVectorStore":
        """
        Load existing vector store from disk
        
        Args:
            embeddings_manager: EmbeddingsManager instance
            config: Store configuration
            
        Returns:
            Loaded RegulationVectorStore instance
        """
        instance = cls(embeddings_manager, config)
        
        vectorstore_path = instance.config.vectorstore_dir / "index.faiss"
        if not vectorstore_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {instance.config.vectorstore_dir}. "
                "Run build_from_source() first."
            )
        
        logger.info(f"Loading vector store from {instance.config.vectorstore_dir}")
        instance._vectorstore = FAISS.load_local(
            str(instance.config.vectorstore_dir),
            embeddings=embeddings_manager.embeddings,
            allow_dangerous_deserialization=True  # Required for pickle loading
        )
        logger.success("Vector store loaded")
        
        return instance
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar documents
        """
        return self.vectorstore.similarity_search(query, k=k, filter=filter)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search with relevance scores
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filter
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add new documents to existing store
        
        Args:
            documents: Documents to add
            
        Returns:
            List of document IDs
        """
        chunks = self.split_documents(documents)
        ids = self.vectorstore.add_documents(chunks)
        logger.info(f"Added {len(chunks)} new chunks to vector store")
        return ids
    
    def delete(self, ids: List[str]) -> bool:
        """
        Delete documents by ID
        
        Args:
            ids: Document IDs to delete
            
        Returns:
            True if successful
        """
        return self.vectorstore.delete(ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics
        
        Returns:
            Dictionary with store stats
        """
        if self._vectorstore is None:
            return {"status": "not_initialized"}
        
        # FAISS index info
        index = self._vectorstore.index
        
        return {
            "status": "initialized",
            "total_vectors": index.ntotal,
            "dimension": index.d,
            "source_dir": str(self.config.source_dir),
            "vectorstore_dir": str(self.config.vectorstore_dir),
        }
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"RegulationVectorStore("
            f"status={stats['status']}, "
            f"vectors={stats.get('total_vectors', 0)})"
        )


class InMemoryDocumentProcessor:
    """
    Ephemeral processor for medical documents (no persistence)
    
    為病歷文件提供臨時處理（不持久化），確保個資不被存儲。
    
    Design Philosophy:
    - Create temporary vector store in memory
    - Process medical document
    - Destroy vector store after use
    - Never persist to disk
    """
    
    def __init__(
        self,
        embeddings_manager: EmbeddingsManager,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize in-memory processor
        
        Args:
            embeddings_manager: EmbeddingsManager instance
            chunk_size: Text chunk size
            chunk_overlap: Chunk overlap
        """
        self.embeddings_manager = embeddings_manager
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def create_temp_store(self, text: str) -> FAISS:
        """
        Create temporary in-memory vector store for a medical document
        
        Args:
            text: Medical document text
            
        Returns:
            FAISS vector store (in-memory, ephemeral)
        """
        # Split text
        chunks = self.text_splitter.split_text(text)
        
        # Create in-memory vector store
        vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=self.embeddings_manager.embeddings
        )
        
        logger.debug(
            f"Created ephemeral vector store with {len(chunks)} chunks "
            "(will be destroyed after use)"
        )
        
        return vectorstore
    
    def process_and_destroy(
        self,
        text: str,
        query: str,
        k: int = 3
    ) -> List[Document]:
        """
        Process medical document and immediately destroy vector store
        
        Args:
            text: Medical document text
            query: Query for semantic search
            k: Number of results
            
        Returns:
            Search results
        """
        # Create temporary store
        temp_store = self.create_temp_store(text)
        
        try:
            # Perform search
            results = temp_store.similarity_search(query, k=k)
            return results
        finally:
            # Explicitly destroy (Python GC will handle, but being explicit)
            del temp_store
            logger.debug("Ephemeral vector store destroyed")
