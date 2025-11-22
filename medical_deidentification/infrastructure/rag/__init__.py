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
- EmbeddingsManager: Embedding model management
- RegulationVectorStore: Persistent storage for regulation documents
- RegulationRetriever: Semantic search for regulations
- RegulationRetrievalChain: Retrieve PHI definitions from regulations
- PHIIdentificationChain: Identify PHI in medical text
- MedicalTextRetriever: Ephemeral medical document processing
"""

from .embeddings import (
    EmbeddingsManager,
    EmbeddingsConfig,
    PretrainedModels,
    create_embeddings_manager
)

from .regulation_store import (
    RegulationVectorStore,
    RegulationStoreConfig,
    InMemoryDocumentProcessor
)

from .regulation_retriever import (
    RegulationRetriever,
    RegulationRetrieverConfig,
    create_regulation_retriever
)

from .medical_retriever import (
    MedicalTextRetriever,
    MedicalRetrieverConfig,
    create_medical_retriever
)

# New modular chains (recommended)
from .regulation_retrieval_chain import (
    RegulationRetrievalChain,
    RegulationRetrievalConfig,
    create_regulation_retrieval_chain
)

from .phi_identification_chain import (
    PHIIdentificationChain,
    PHIIdentificationConfig,
    PHIIdentificationResult,
    PHIDetectionResponse,
    create_phi_identification_chain
)

__all__ = [
    # Embeddings
    "EmbeddingsManager",
    "EmbeddingsConfig",
    "PretrainedModels",
    "create_embeddings_manager",
    
    # Vector Store
    "RegulationVectorStore",
    "RegulationStoreConfig",
    "InMemoryDocumentProcessor",
    
    # Regulation Retriever (persistent)
    "RegulationRetriever",
    "RegulationRetrieverConfig",
    "create_regulation_retriever",
    
    # Medical Retriever (ephemeral)
    "MedicalTextRetriever",
    "MedicalRetrieverConfig",
    "create_medical_retriever",
    
    # New Modular Chains (recommended)
    "RegulationRetrievalChain",
    "RegulationRetrievalConfig",
    "create_regulation_retrieval_chain",
    "PHIIdentificationChain",
    "PHIIdentificationConfig",
    "PHIIdentificationResult",
    "PHIDetectionResponse",
    "create_phi_identification_chain",
]

