"""
Base Classes for Document Loader
文件載入器基礎類別

Defines abstract interfaces and common data structures for all document loaders.
定義所有文件載入器的抽象接口和通用數據結構。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# Import domain models
from ...domain.loader_models import (
    DocumentFormat,
    LoadedDocument,
    LoaderConfig,
)


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders
    文件載入器抽象基類
    
    All format-specific loaders must inherit from this class and implement
    the load() method.
    
    所有格式特定的載入器必須繼承此類並實作 load() 方法。
    """

    def __init__(self, config: LoaderConfig | None = None):
        """
        Initialize loader
        
        Args:
            config: Loader configuration. Uses defaults if None.
        """
        self.config = config or LoaderConfig()

    @abstractmethod
    def load(self, file_path: str | Path) -> LoadedDocument:
        """
        Load document from file
        
        Args:
            file_path: Path to the document file
            
        Returns:
            LoadedDocument with content and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
            IOError: If file cannot be read
        """
        pass

    @abstractmethod
    def supports_format(self, format: DocumentFormat) -> bool:
        """
        Check if loader supports the given format
        
        Args:
            format: Document format to check
            
        Returns:
            True if supported, False otherwise
        """
        pass

    def load_multiple(self, file_paths: list[str | Path]) -> list[LoadedDocument]:
        """
        Load multiple documents
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of LoadedDocument objects
        """
        documents = []
        for file_path in file_paths:
            try:
                doc = self.load(file_path)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        return documents

    def _extract_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """
        Extract file metadata from filesystem
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file metadata
        """
        if not self.config.extract_metadata:
            return {}

        stat = file_path.stat()

        return {
            "filename": file_path.name,
            "filepath": file_path,
            "file_size": stat.st_size,
            "format": DocumentFormat.from_extension(file_path.suffix),
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "encoding": self.config.encoding,
        }

    def _validate_file(self, file_path: Path) -> None:
        """
        Validate file exists and is readable
        
        Args:
            file_path: Path to file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        if self.config.max_file_size is not None:
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                raise ValueError(
                    f"File too large: {file_size} bytes "
                    f"(max: {self.config.max_file_size} bytes)"
                )

    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(config={self.config})"


class BaseTextLoader(DocumentLoader):
    """
    Base class for text-based loaders
    文字型載入器基類
    
    Provides common functionality for loaders that extract plain text.
    """

    def _read_text_file(self, file_path: Path) -> str:
        """
        Read text file with encoding handling
        
        Args:
            file_path: Path to text file
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, encoding=self.config.encoding,
                     errors=self.config.encoding_errors) as f:
                content = f.read()

            if not self.config.preserve_formatting:
                # Normalize whitespace
                content = ' '.join(content.split())

            return content

        except UnicodeDecodeError:
            logger.warning(
                f"Failed to decode {file_path} with {self.config.encoding}, "
                f"trying with latin-1"
            )
            with open(file_path, encoding='latin-1') as f:
                return f.read()


class BaseBinaryLoader(DocumentLoader):
    """
    Base class for binary file loaders
    二進位檔案載入器基類
    
    Provides common functionality for loaders that handle binary files.
    """

    def _read_binary_file(self, file_path: Path) -> bytes:
        """
        Read binary file
        
        Args:
            file_path: Path to binary file
            
        Returns:
            File content as bytes
        """
        with open(file_path, 'rb') as f:
            return f.read()
