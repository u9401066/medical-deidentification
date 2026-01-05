"""
Medical Text Splitter Utility
醫療文本分割工具

Lightweight text splitting for medical documents.
輕量級醫療文檔分割。
"""


from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from ...domain import MedicalRetrieverConfig


class MedicalTextSplitter:
    """
    Medical document text splitter
    醫療文檔文本分割器
    
    Optimized for medical contexts:
    - Smaller chunks (default 500 chars)
    - Medical-friendly separators (paragraph → sentence → clause)
    - Configurable overlap to preserve context
    
    針對醫療文本優化：
    - 較小的 chunk（預設 500 字元）
    - 醫療友好的分隔符（段落 → 句子 → 子句）
    - 可配置的重疊以保留上下文
    
    Examples:
        >>> from core.infrastructure.rag import MedicalTextSplitter
        >>> 
        >>> # Default settings
        >>> splitter = MedicalTextSplitter()
        >>> chunks = splitter.split_text("Patient John Smith...")
        >>> 
        >>> # Custom settings
        >>> splitter = MedicalTextSplitter(chunk_size=1000, chunk_overlap=100)
        >>> chunks = splitter.split_text(text)
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize medical text splitter
        
        Args:
            chunk_size: Size of each text chunk (default: 500 for medical docs)
            chunk_overlap: Overlap between chunks (default: 50)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

        logger.debug(
            f"[TextSplitter] Initialized "
            f"(chunk_size={chunk_size}, chunk_overlap={chunk_overlap})"
        )

    @classmethod
    def from_config(cls, config: MedicalRetrieverConfig) -> "MedicalTextSplitter":
        """
        Create splitter from MedicalRetrieverConfig
        
        Args:
            config: Configuration with chunk_size and chunk_overlap
            
        Returns:
            Configured MedicalTextSplitter
        """
        return cls(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )

    def split_text(self, text: str) -> list[str]:
        """
        Split medical text into chunks
        
        Args:
            text: Medical document text
            
        Returns:
            List of text chunks
            
        Examples:
            >>> splitter = MedicalTextSplitter(chunk_size=500)
            >>> chunks = splitter.split_text("Long medical document...")
            >>> len(chunks)
            5
        """
        chunks = self._text_splitter.split_text(text)
        logger.debug(
            f"[TextSplitter] Split {len(text)} chars → {len(chunks)} chunks"
        )
        return chunks

    def get_chunk_count(self, text: str) -> int:
        """
        Get estimated number of chunks without splitting
        
        Args:
            text: Medical document text
            
        Returns:
            Estimated chunk count
        """
        estimated = max(1, len(text) // (self.chunk_size - self.chunk_overlap))
        return estimated

    def __repr__(self) -> str:
        return (
            f"MedicalTextSplitter("
            f"chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap})"
        )


def create_medical_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> MedicalTextSplitter:
    """
    Factory function to create medical text splitter
    
    Args:
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        Configured MedicalTextSplitter
        
    Examples:
        >>> splitter = create_medical_splitter(chunk_size=1000)
    """
    return MedicalTextSplitter(chunk_size, chunk_overlap)
