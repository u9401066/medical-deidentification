"""
Base Classes for Document Loader
文件載入器基礎類別

Defines abstract interfaces and common data structures for all document loaders.
定義所有文件載入器的抽象接口和通用數據結構。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from loguru import logger


class DocumentFormat(str, Enum):
    """支援的文件格式 | Supported document formats"""
    TXT = "txt"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    DOCX = "docx"
    JSON = "json"
    PDF = "pdf"
    HTML = "html"
    XML = "xml"
    FHIR = "fhir"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_extension(cls, extension: str) -> "DocumentFormat":
        """
        Get format from file extension
        
        Args:
            extension: File extension (with or without dot)
            
        Returns:
            DocumentFormat enum
        """
        ext = extension.lower().lstrip('.')
        try:
            return cls(ext)
        except ValueError:
            return cls.UNKNOWN


class DocumentMetadata(BaseModel):
    """
    Document metadata
    文件元數據
    
    Stores information about the source document including:
    - File information (path, size, format)
    - Temporal information (created, modified, loaded)
    - Content information (encoding, language)
    - Custom metadata from source
    """
    
    # File information
    filename: str = Field(description="Original filename")
    filepath: Optional[Path] = Field(default=None, description="Full file path")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    format: DocumentFormat = Field(description="Document format")
    
    # Temporal information
    created_at: Optional[datetime] = Field(default=None, description="File creation time")
    modified_at: Optional[datetime] = Field(default=None, description="File modification time")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When loaded")
    
    # Content information
    encoding: str = Field(default="utf-8", description="Text encoding")
    language: Optional[str] = Field(default=None, description="Document language (e.g., 'zh-TW', 'en')")
    
    # Sheet/page information (for multi-part documents)
    sheet_name: Optional[str] = Field(default=None, description="Excel sheet name")
    page_number: Optional[int] = Field(default=None, description="PDF page number")
    
    # Custom metadata
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    
    class Config:
        arbitrary_types_allowed = True


class LoadedDocument(BaseModel):
    """
    Loaded document with content and metadata
    載入的文件（包含內容和元數據）
    
    Represents a document that has been successfully loaded and parsed.
    """
    
    content: str = Field(description="Document text content")
    metadata: DocumentMetadata = Field(description="Document metadata")
    
    # Optional structured data (for CSV, JSON, etc.)
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured data (for CSV, JSON, etc.)"
    )
    
    # Optional multiple records (for CSV with multiple rows)
    records: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Multiple records (e.g., CSV rows)"
    )
    
    def __str__(self) -> str:
        """String representation"""
        return f"LoadedDocument(filename={self.metadata.filename}, length={len(self.content)})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (
            f"LoadedDocument(filename={self.metadata.filename}, "
            f"format={self.metadata.format.value}, "
            f"length={len(self.content)}, "
            f"has_structured_data={self.structured_data is not None}, "
            f"num_records={len(self.records) if self.records else 0})"
        )


class LoaderConfig(BaseModel):
    """
    Configuration for document loaders
    文件載入器配置
    """
    
    # Encoding
    encoding: str = Field(default="utf-8", description="Text encoding")
    encoding_errors: str = Field(
        default="replace",
        description="How to handle encoding errors: 'strict', 'ignore', 'replace'"
    )
    
    # Content extraction
    extract_metadata: bool = Field(default=True, description="Extract file metadata")
    preserve_formatting: bool = Field(default=False, description="Preserve formatting (spaces, newlines)")
    
    # Excel-specific
    excel_sheet_name: Optional[str] = Field(
        default=None,
        description="Specific sheet to load (None = all sheets)"
    )
    excel_skip_rows: int = Field(default=0, description="Rows to skip in Excel")
    
    # CSV-specific
    csv_delimiter: str = Field(default=",", description="CSV delimiter")
    csv_quotechar: str = Field(default='"', description="CSV quote character")
    csv_has_header: bool = Field(default=True, description="CSV has header row")
    
    # PDF-specific
    pdf_extract_images: bool = Field(default=False, description="Extract images from PDF")
    pdf_page_range: Optional[tuple[int, int]] = Field(
        default=None,
        description="Page range to extract (start, end)"
    )
    
    # HTML-specific
    html_extract_text_only: bool = Field(default=True, description="Extract text only from HTML")
    html_remove_scripts: bool = Field(default=True, description="Remove script tags")
    
    # Performance
    max_file_size: Optional[int] = Field(
        default=None,
        description="Max file size in bytes (None = unlimited)"
    )
    
    class Config:
        arbitrary_types_allowed = True


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders
    文件載入器抽象基類
    
    All format-specific loaders must inherit from this class and implement
    the load() method.
    
    所有格式特定的載入器必須繼承此類並實作 load() 方法。
    """
    
    def __init__(self, config: Optional[LoaderConfig] = None):
        """
        Initialize loader
        
        Args:
            config: Loader configuration. Uses defaults if None.
        """
        self.config = config or LoaderConfig()
    
    @abstractmethod
    def load(self, file_path: Union[str, Path]) -> LoadedDocument:
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
    
    def load_multiple(self, file_paths: List[Union[str, Path]]) -> List[LoadedDocument]:
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
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
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
            with open(file_path, 'r', encoding=self.config.encoding, 
                     errors=self.config.encoding_errors) as f:
                content = f.read()
            
            if not self.config.preserve_formatting:
                # Normalize whitespace
                content = ' '.join(content.split())
            
            return content
        
        except UnicodeDecodeError as e:
            logger.warning(
                f"Failed to decode {file_path} with {self.config.encoding}, "
                f"trying with latin-1"
            )
            with open(file_path, 'r', encoding='latin-1') as f:
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
