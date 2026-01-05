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
- EmbeddingsManager: Embedding model management (lazy import to avoid torch)
- RegulationVectorStore: Persistent storage for regulation documents
- RegulationRetriever: Semantic search for regulations
- RegulationRetrievalChain: Retrieve PHI definitions from regulations
- PHIIdentificationChain: Identify PHI in medical text
- MedicalTextRetriever: Ephemeral medical document processing

Note: Uses lazy imports to avoid torch/transformers import conflicts.
注意：使用延遲導入以避免 torch/transformers 導入衝突。
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid torch/transformers conflicts at module load time
# 延遲導入以避免模組載入時的 torch/transformers 衝突

if TYPE_CHECKING:
    # Type hints only (not imported at runtime)
    from .embeddings import (
        EmbeddingsConfig,
        EmbeddingsManager,
        PretrainedModels,
        create_embeddings_manager,
    )
    from .medical_retriever import (
        MedicalRetrieverConfig,
        MedicalTextRetriever,
        create_medical_retriever,
    )
    from .phi_agent import PHIIdentificationAgent
    from .phi_identification_chain import PHIIdentificationChain
    from .regulation_retrieval_chain import (
        RegulationRetrievalChain,
        RegulationRetrievalConfig,
        create_regulation_retrieval_chain,
    )
    from .regulation_retriever import (
        RegulationRetriever,
        RegulationRetrieverConfig,
        create_regulation_retriever,
    )
    from .regulation_store import (
        InMemoryDocumentProcessor,
        RegulationStoreConfig,
        RegulationVectorStore,
    )
    from .text_splitter import MedicalTextSplitter, create_medical_splitter


def __getattr__(name: str):
    """
    Lazy import implementation to avoid torch/transformers conflicts
    延遲導入實現以避免 torch/transformers 衝突
    """
    # Embeddings (requires torch/transformers)
    if name in ("EmbeddingsManager", "EmbeddingsConfig", "PretrainedModels", "create_embeddings_manager"):
        from . import embeddings
        return getattr(embeddings, name)

    # Regulation Store
    if name in ("RegulationVectorStore", "RegulationStoreConfig", "InMemoryDocumentProcessor"):
        from . import regulation_store
        return getattr(regulation_store, name)

    # Regulation Retriever
    if name in ("RegulationRetriever", "RegulationRetrieverConfig", "create_regulation_retriever"):
        from . import regulation_retriever
        return getattr(regulation_retriever, name)

    # Text Splitter
    if name in ("MedicalTextSplitter", "create_medical_splitter"):
        from . import text_splitter
        return getattr(text_splitter, name)

    # Medical Retriever
    if name in ("MedicalTextRetriever", "MedicalRetrieverConfig", "create_medical_retriever"):
        from . import medical_retriever
        return getattr(medical_retriever, name)

    # Regulation Retrieval Chain
    if name in ("RegulationRetrievalChain", "RegulationRetrievalConfig", "create_regulation_retrieval_chain"):
        from . import regulation_retrieval_chain
        return getattr(regulation_retrieval_chain, name)

    # PHI Identification Chain
    if name == "PHIIdentificationChain":
        from .phi_identification_chain import PHIIdentificationChain
        return PHIIdentificationChain

    # PHI Agent
    if name == "PHIIdentificationAgent":
        from .phi_agent import PHIIdentificationAgent
        return PHIIdentificationAgent

    # Domain models (safe to import directly - no torch dependency)
    if name in ("PHIIdentificationConfig", "PHIIdentificationResult", "PHIDetectionResponse"):
        from ...domain.phi_identification_models import (
            PHIDetectionResponse,
            PHIIdentificationConfig,
            PHIIdentificationResult,
        )
        mapping = {
            "PHIIdentificationConfig": PHIIdentificationConfig,
            "PHIIdentificationResult": PHIIdentificationResult,
            "PHIDetectionResponse": PHIDetectionResponse,
        }
        return mapping[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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

    # Text Splitting
    "MedicalTextSplitter",
    "create_medical_splitter",

    # Medical Retriever (ephemeral, for future RAG use)
    "MedicalTextRetriever",
    "MedicalRetrieverConfig",
    "create_medical_retriever",

    # New Modular Chains (recommended)
    "RegulationRetrievalChain",
    "RegulationRetrievalConfig",
    "create_regulation_retrieval_chain",
    "PHIIdentificationChain",
    "PHIIdentificationAgent",  # Agent with tool-calling
    "PHIIdentificationConfig",
    "PHIIdentificationResult",
    "PHIDetectionResponse",
]

