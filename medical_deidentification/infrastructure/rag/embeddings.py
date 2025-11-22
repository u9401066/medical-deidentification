"""
Embeddings Manager
嵌入模型管理器

Manages embedding models for semantic similarity search in RAG system.
管理用於 RAG 系統語義相似度搜索的嵌入模型。
"""

from typing import Optional, List
from langchain_community.embeddings import HuggingFaceEmbeddings
from pydantic import BaseModel, Field


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
    cache_folder: Optional[str] = Field(
        default=None,
        description="Local cache folder for downloaded models"
    )


class EmbeddingsManager:
    """
    Embeddings Manager for RAG System
    
    Provides unified interface for embedding model management.
    Supports HuggingFace sentence-transformers models for multilingual support.
    
    為 RAG 系統提供統一的嵌入模型管理介面。
    支援 HuggingFace sentence-transformers 多語言模型。
    """
    
    def __init__(self, config: Optional[EmbeddingsConfig] = None):
        """
        Initialize embeddings manager
        
        Args:
            config: Embeddings configuration. Uses defaults if None.
        """
        self.config = config or EmbeddingsConfig()
        self._embeddings: Optional[HuggingFaceEmbeddings] = None
    
    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """
        Get or create embeddings model (lazy loading)
        
        Returns:
            HuggingFaceEmbeddings instance
        """
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.config.model_name,
                model_kwargs=self.config.model_kwargs,
                encode_kwargs=self.config.encode_kwargs,
                cache_folder=self.config.cache_folder
            )
        return self._embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query text
        
        Args:
            text: Query text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
    
    @property
    def dimension(self) -> int:
        """
        Get embedding dimension
        
        Returns:
            Embedding vector dimension
        """
        # Embed a test query to get dimension
        test_embedding = self.embed_query("test")
        return len(test_embedding)
    
    def __repr__(self) -> str:
        return f"EmbeddingsManager(model={self.config.model_name}, device={self.config.model_kwargs.get('device')})"


# Predefined model configurations
class PretrainedModels:
    """預訓練模型配置"""
    
    # Multilingual model (recommended for medical documents with mixed languages)
    MULTILINGUAL_MPNET = EmbeddingsConfig(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={"device": "cpu"}
    )
    
    # Medical domain-specific model
    BIOMEDICAL_PUBMED = EmbeddingsConfig(
        model_name="pritamdeka/PubMedBERT-mnli-snli-scinli-scitail-mednli-stsb",
        model_kwargs={"device": "cpu"}
    )
    
    # Lightweight model for faster processing
    MINILM_L6 = EmbeddingsConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    
    # English-only high-performance model
    MPNET_BASE = EmbeddingsConfig(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={"device": "cpu"}
    )


def create_embeddings_manager(
    model_preset: str = "multilingual",
    device: str = "cpu"
) -> EmbeddingsManager:
    """
    Factory function to create embeddings manager with preset configuration
    
    Args:
        model_preset: Preset name ('multilingual', 'biomedical', 'lightweight', 'english')
        device: Device to use ('cpu' or 'cuda')
        
    Returns:
        Configured EmbeddingsManager instance
    """
    preset_map = {
        "multilingual": PretrainedModels.MULTILINGUAL_MPNET,
        "biomedical": PretrainedModels.BIOMEDICAL_PUBMED,
        "lightweight": PretrainedModels.MINILM_L6,
        "english": PretrainedModels.MPNET_BASE,
    }
    
    if model_preset not in preset_map:
        raise ValueError(
            f"Unknown model preset: {model_preset}. "
            f"Choose from: {list(preset_map.keys())}"
        )
    
    config = preset_map[model_preset]
    config.model_kwargs["device"] = device
    
    return EmbeddingsManager(config)
