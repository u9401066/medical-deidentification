"""
Module 1: Document Loader | 文件載入模組

Multi-format document loader for medical records with metadata extraction.
多格式醫療文件載入器，支援元數據提取。

Supported Formats:
- TXT: Plain text files
- CSV: Comma-separated values
- XLSX/XLS: Excel spreadsheets (multi-sheet support)
- DOCX: Microsoft Word documents
- JSON: Structured JSON medical records
- PDF: Portable Document Format (with text extraction)
- HTML: Web-based medical records
- XML: Structured XML data
- FHIR: FHIR R4 JSON resources

Features:
- Automatic format detection
- Metadata extraction (filename, date, format, etc.)
- Multi-sheet Excel support
- Batch loading from directories
- Error handling and validation
"""

from .base import (
    DocumentFormat,  # Add DocumentFormat export
    DocumentLoader,
    DocumentMetadata,
    LoadedDocument,
    LoaderConfig,
)
from .factory import (
    DocumentLoaderFactory,
    create_loader,
    load_document,
    load_documents_from_directory,
)
from .loaders import (
    CSVLoader,
    ExcelLoader,
    FHIRLoader,
    HTMLLoader,
    JSONLoader,
    PDFLoader,
    TextLoader,
    WordLoader,
    XMLLoader,
)

__all__ = [
    # Base classes
    "DocumentLoader",
    "LoadedDocument",
    "DocumentMetadata",
    "LoaderConfig",
    "DocumentFormat",  # Add to exports

    # Format-specific loaders
    "TextLoader",
    "CSVLoader",
    "ExcelLoader",
    "WordLoader",
    "JSONLoader",
    "PDFLoader",
    "HTMLLoader",
    "XMLLoader",
    "FHIRLoader",

    # Factory and utilities
    "DocumentLoaderFactory",
    "create_loader",
    "load_document",
    "load_documents_from_directory",
]

