"""
Domain Configuration Models
領域配置模型

Centralized configuration classes for all domain-related operations.
All configuration BaseModel classes belong here (DDD principle).

集中管理所有領域相關操作的配置類別。
所有配置 BaseModel 類別都屬於這裡（DDD 原則）。
"""

from pathlib import Path

from pydantic import BaseModel, Field

# ============================================================================
# RAG Configuration Models
# ============================================================================

class EmbeddingsConfig(BaseModel):
    """嵌入模型配置"""

    model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        description="HuggingFace model name for embeddings"
    )
    model_kwargs: dict = Field(
        default_factory=lambda: {"device": "cpu"},
        description="Additional model kwargs (e.g., device: 'cpu' or 'cuda')"
    )
    encode_kwargs: dict = Field(
        default_factory=lambda: {"normalize_embeddings": True},
        description="Encoding kwargs for generating embeddings"
    )
    cache_folder: str | None = Field(
        default=None,
        description="Local cache folder for downloaded models"
    )


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
    file_patterns: list[str] = Field(
        default_factory=lambda: ["**/*.md", "**/*.txt"],
        description="File patterns to load"
    )


class RegulationRetrieverConfig(BaseModel):
    """法規檢索器配置"""

    search_type: str = Field(
        default="mmr",
        description="Search type: 'similarity' or 'mmr' (Maximal Marginal Relevance)"
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of documents to retrieve"
    )
    fetch_k: int = Field(
        default=20,
        ge=1,
        description="Number of documents to fetch before MMR filtering"
    )
    lambda_mult: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Lambda multiplier for MMR (0=diversity, 1=relevance)"
    )
    score_threshold: float | None = Field(
        default=None,
        description="Minimum relevance score threshold"
    )


class RegulationRetrievalConfig(BaseModel):
    """法規檢索鏈配置"""

    retriever_config: RegulationRetrieverConfig = Field(
        default_factory=RegulationRetrieverConfig,
        description="Retriever configuration"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of regulation documents to retrieve"
    )
    min_relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score threshold"
    )


class MedicalRetrieverConfig(BaseModel):
    """醫療文本檢索器配置"""

    search_type: str = Field(
        default="similarity",
        description="Search type: 'similarity' (MMR not recommended for small medical docs)"
    )
    k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of chunks to retrieve (smaller for medical docs)"
    )
    score_threshold: float | None = Field(
        default=None,
        description="Minimum relevance score threshold"
    )
    chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Text chunk size for medical documents"
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between chunks"
    )




__all__ = [
    # RAG Configs
    "EmbeddingsConfig",
    "RegulationStoreConfig",
    "RegulationRetrieverConfig",
    "RegulationRetrievalConfig",
    "MedicalRetrieverConfig",
]
