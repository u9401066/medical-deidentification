"""
Document Loader Factory
文件載入器工廠

Provides factory methods and utilities for creating and using document loaders.
提供創建和使用文件載入器的工廠方法和工具。
"""

from pathlib import Path
from typing import Union, List, Optional, Dict, Type
from loguru import logger

from .base import DocumentLoader, LoadedDocument, DocumentFormat, LoaderConfig
from .loaders import (
    TextLoader,
    CSVLoader,
    ExcelLoader,
    WordLoader,
    JSONLoader,
    PDFLoader,
    HTMLLoader,
    XMLLoader,
    FHIRLoader
)


class DocumentLoaderFactory:
    """
    Factory for creating document loaders
    文件載入器工廠
    
    Automatically selects the appropriate loader based on file extension
    or specified format.
    
    Examples:
        >>> factory = DocumentLoaderFactory()
        >>> loader = factory.create_loader("patient.xlsx")
        >>> doc = loader.load("patient.xlsx")
        >>> 
        >>> # Or use convenience method
        >>> doc = factory.load("patient.xlsx")
    """
    
    # Mapping of formats to loader classes
    _LOADER_REGISTRY: Dict[DocumentFormat, Type[DocumentLoader]] = {
        DocumentFormat.TXT: TextLoader,
        DocumentFormat.CSV: CSVLoader,
        DocumentFormat.XLSX: ExcelLoader,
        DocumentFormat.XLS: ExcelLoader,
        DocumentFormat.DOCX: WordLoader,
        DocumentFormat.JSON: JSONLoader,
        DocumentFormat.PDF: PDFLoader,
        DocumentFormat.HTML: HTMLLoader,
        DocumentFormat.XML: XMLLoader,
        DocumentFormat.FHIR: FHIRLoader,
    }
    
    def __init__(self, default_config: Optional[LoaderConfig] = None):
        """
        Initialize factory
        
        Args:
            default_config: Default configuration for all loaders
        """
        self.default_config = default_config or LoaderConfig()
    
    def create_loader(
        self,
        file_path: Union[str, Path],
        format: Optional[DocumentFormat] = None,
        config: Optional[LoaderConfig] = None
    ) -> DocumentLoader:
        """
        Create appropriate loader for file
        
        Args:
            file_path: Path to file (for extension detection)
            format: Explicit format (overrides extension detection)
            config: Loader configuration (uses default if None)
            
        Returns:
            DocumentLoader instance
            
        Raises:
            ValueError: If format is unsupported
        """
        file_path = Path(file_path)
        
        # Determine format
        if format is None:
            format = DocumentFormat.from_extension(file_path.suffix)
        
        # Special case: detect FHIR from JSON
        if format == DocumentFormat.JSON and self._is_fhir_file(file_path):
            format = DocumentFormat.FHIR
        
        # Get loader class
        if format not in self._LOADER_REGISTRY:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported: {list(self._LOADER_REGISTRY.keys())}"
            )
        
        loader_class = self._LOADER_REGISTRY[format]
        
        # Create loader with config
        loader_config = config or self.default_config
        loader = loader_class(loader_config)
        
        logger.debug(f"Created {loader_class.__name__} for {file_path}")
        
        return loader
    
    def load(
        self,
        file_path: Union[str, Path],
        format: Optional[DocumentFormat] = None,
        config: Optional[LoaderConfig] = None
    ) -> LoadedDocument:
        """
        Convenience method: create loader and load document
        
        Args:
            file_path: Path to file
            format: Explicit format
            config: Loader configuration
            
        Returns:
            LoadedDocument
        """
        loader = self.create_loader(file_path, format, config)
        return loader.load(file_path)
    
    def load_multiple(
        self,
        file_paths: List[Union[str, Path]],
        config: Optional[LoaderConfig] = None
    ) -> List[LoadedDocument]:
        """
        Load multiple documents
        
        Args:
            file_paths: List of file paths
            config: Loader configuration
            
        Returns:
            List of LoadedDocument objects
        """
        documents = []
        
        for file_path in file_paths:
            try:
                doc = self.load(file_path, config=config)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        logger.info(f"Loaded {len(documents)}/{len(file_paths)} documents")
        return documents
    
    def load_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False,
        config: Optional[LoaderConfig] = None
    ) -> List[LoadedDocument]:
        """
        Load all documents from directory
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., "*.txt", "*.xlsx")
            recursive: Search subdirectories
            config: Loader configuration
            
        Returns:
            List of LoadedDocument objects
        """
        directory = Path(directory)
        
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        # Find files
        if recursive:
            file_paths = list(directory.rglob(pattern))
        else:
            file_paths = list(directory.glob(pattern))
        
        # Filter out directories
        file_paths = [p for p in file_paths if p.is_file()]
        
        logger.info(f"Found {len(file_paths)} files in {directory}")
        
        return self.load_multiple(file_paths, config=config)
    
    def _is_fhir_file(self, file_path: Path) -> bool:
        """
        Check if JSON file is FHIR resource
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            True if FHIR, False otherwise
        """
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
                return "resourceType" in data
        except Exception:
            return False
    
    @classmethod
    def register_loader(
        cls,
        format: DocumentFormat,
        loader_class: Type[DocumentLoader]
    ) -> None:
        """
        Register custom loader for format
        
        Args:
            format: Document format
            loader_class: Loader class (must inherit from DocumentLoader)
        """
        if not issubclass(loader_class, DocumentLoader):
            raise TypeError(
                f"Loader class must inherit from DocumentLoader, "
                f"got {loader_class}"
            )
        
        cls._LOADER_REGISTRY[format] = loader_class
        logger.info(f"Registered {loader_class.__name__} for {format}")
    
    @classmethod
    def get_supported_formats(cls) -> List[DocumentFormat]:
        """Get list of supported formats"""
        return list(cls._LOADER_REGISTRY.keys())
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions"""
        return [fmt.value for fmt in cls._LOADER_REGISTRY.keys() 
                if fmt != DocumentFormat.UNKNOWN]


# Convenience functions
# 便利函數

def create_loader(
    file_path: Union[str, Path],
    format: Optional[DocumentFormat] = None,
    config: Optional[LoaderConfig] = None
) -> DocumentLoader:
    """
    Create document loader for file
    
    Args:
        file_path: Path to file
        format: Explicit format
        config: Loader configuration
        
    Returns:
        DocumentLoader instance
    
    Examples:
        >>> loader = create_loader("patient.xlsx")
        >>> doc = loader.load("patient.xlsx")
    """
    factory = DocumentLoaderFactory(default_config=config)
    return factory.create_loader(file_path, format)


def load_document(
    file_path: Union[str, Path],
    format: Optional[DocumentFormat] = None,
    config: Optional[LoaderConfig] = None
) -> LoadedDocument:
    """
    Load single document
    
    Args:
        file_path: Path to file
        format: Explicit format
        config: Loader configuration
        
    Returns:
        LoadedDocument
    
    Examples:
        >>> doc = load_document("patient.xlsx")
        >>> print(doc.content)
        >>> print(doc.records[0])
    """
    factory = DocumentLoaderFactory(default_config=config)
    return factory.load(file_path, format)


def load_documents_from_directory(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
    config: Optional[LoaderConfig] = None
) -> List[LoadedDocument]:
    """
    Load all documents from directory
    
    Args:
        directory: Directory path
        pattern: File pattern (e.g., "*.txt", "*.xlsx")
        recursive: Search subdirectories
        config: Loader configuration
        
    Returns:
        List of LoadedDocument objects
    
    Examples:
        >>> # Load all Excel files
        >>> docs = load_documents_from_directory("data/", pattern="*.xlsx")
        >>> 
        >>> # Load all files recursively
        >>> docs = load_documents_from_directory("data/", pattern="*", recursive=True)
    """
    factory = DocumentLoaderFactory(default_config=config)
    return factory.load_directory(directory, pattern, recursive)


def get_supported_formats() -> List[str]:
    """
    Get list of supported file formats
    
    Returns:
        List of format names
    
    Examples:
        >>> formats = get_supported_formats()
        >>> print(formats)
        ['txt', 'csv', 'xlsx', 'xls', 'docx', 'json', 'pdf', 'html', 'xml', 'fhir']
    """
    return [fmt.value for fmt in DocumentLoaderFactory.get_supported_formats()
            if fmt != DocumentFormat.UNKNOWN]
