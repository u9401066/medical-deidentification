"""
Domain Models for Document Loading
文檔載入相關的領域模型

Contains all domain models related to document loading and metadata.
包含所有與文檔載入和元數據相關的領域模型。
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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
    filepath: Path | None = Field(default=None, description="Full file path")
    file_size: int | None = Field(default=None, description="File size in bytes")
    format: DocumentFormat = Field(description="Document format")

    # Temporal information
    created_at: datetime | None = Field(default=None, description="File creation time")
    modified_at: datetime | None = Field(default=None, description="File modification time")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When loaded")

    # Content information
    encoding: str = Field(default="utf-8", description="Text encoding")
    language: str | None = Field(default=None, description="Document language (e.g., 'zh-TW', 'en')")

    # Sheet/page information (for multi-part documents)
    sheet_name: str | None = Field(default=None, description="Excel sheet name")
    page_number: int | None = Field(default=None, description="PDF page number")

    # Custom metadata
    custom: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

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
    structured_data: dict[str, Any] | None = Field(
        default=None,
        description="Structured data (for CSV, JSON, etc.)"
    )

    # Optional multiple records (for CSV with multiple rows)
    records: list[dict[str, Any]] | None = Field(
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
    excel_sheet_name: str | None = Field(
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
    pdf_page_range: tuple[int, int] | None = Field(
        default=None,
        description="Page range to extract (start, end)"
    )

    # HTML-specific
    html_extract_text_only: bool = Field(default=True, description="Extract text only from HTML")
    html_remove_scripts: bool = Field(default=True, description="Remove script tags")

    # Performance
    max_file_size: int | None = Field(
        default=None,
        description="Max file size in bytes (None = unlimited)"
    )

    class Config:
        arbitrary_types_allowed = True


__all__ = [
    "DocumentFormat",
    "DocumentMetadata",
    "LoadedDocument",
    "LoaderConfig",
]
