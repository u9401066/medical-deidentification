"""
Module 2: RAG Regulation Engine | RAG 規範引擎

RAG-based regulation retrieval for context-aware de-identification.
基於 RAG 的法規檢索,用於上下文感知的去識別化。

This is the innovative core that retrieves "what to mask" from regulation documents.
這是從法規文件檢索「需要遮蔽內容」的創新核心。

Architecture:
- LangChain framework for unified LLM/RAG/Agent management
- FAISS for persistent regulation vector store
- HuggingFace embeddings for semantic search
- In-memory processing for medical documents (no persistence)

Components:
- RegulationVectorStore: Persistent storage for regulation documents
- RegulationRetriever: Semantic search and retrieval
- EmbeddingsManager: Embedding model management
- InMemoryProcessor: Ephemeral medical document processing
"""

from .embeddings import EmbeddingsManager
from .regulation_store import RegulationVectorStore
from .retriever import RegulationRetriever

__all__ = [
    "EmbeddingsManager",
    "RegulationVectorStore",
    "RegulationRetriever",
]

