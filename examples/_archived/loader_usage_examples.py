"""
Document Loader Usage Examples
文件載入器使用範例

Demonstrates how to load various document formats for medical de-identification.
示範如何載入各種文件格式進行醫療去識別化。
"""

from pathlib import Path
from core.infrastructure.loader import (
    # Base classes
    LoaderConfig,
    DocumentFormat,
    
    # Specific loaders
    TextLoader,
    CSVLoader,
    ExcelLoader,
    WordLoader,
    JSONLoader,
    PDFLoader,
    HTMLLoader,
    XMLLoader,
    FHIRLoader,
    
    # Factory and utilities
    create_loader,
    load_document,
    load_documents_from_directory,
    get_supported_formats
)


def example_1_load_text_file():
    """
    Example 1: Load plain text file
    範例 1：載入純文字檔案
    """
    print("=== Example 1: Load TXT File ===\n")
    
    # Simple loading
    doc = load_document("data/test/sample_record.txt")
    
    print(f"Filename: {doc.metadata.filename}")
    print(f"Format: {doc.metadata.format.value}")
    print(f"File size: {doc.metadata.file_size} bytes")
    print(f"Content length: {len(doc.content)} chars")
    print(f"\nContent preview:\n{doc.content[:200]}...")
    print()


def example_2_load_csv_file():
    """
    Example 2: Load CSV file with records
    範例 2：載入 CSV 檔案（含記錄）
    """
    print("=== Example 2: Load CSV File ===\n")
    
    # Configure CSV loading
    config = LoaderConfig(
        csv_delimiter=",",
        csv_has_header=True
    )
    
    # Load CSV
    doc = load_document("data/test/patient_list.csv", config=config)
    
    print(f"Loaded {len(doc.records)} records")
    print(f"\nFirst record:")
    print(doc.records[0])
    
    print(f"\nText representation:")
    print(doc.content[:300])
    print()


def example_3_load_excel_all_sheets():
    """
    Example 3: Load Excel file (all sheets)
    範例 3：載入 Excel 檔案（所有工作表）
    """
    print("=== Example 3: Load Excel (All Sheets) ===\n")
    
    # Load all sheets
    doc = load_document("data/test/test_medical_records_multilang.xlsx")
    
    print(f"File: {doc.metadata.filename}")
    print(f"Sheets: {doc.metadata.custom.get('sheet_names', [])}")
    print(f"Total records: {doc.metadata.custom.get('num_records', 0)}")
    
    if doc.records:
        print(f"\nFirst record:")
        for key, value in list(doc.records[0].items())[:3]:
            print(f"  {key}: {value}")
    
    print()


def example_4_load_excel_specific_sheet():
    """
    Example 4: Load specific Excel sheet
    範例 4：載入特定 Excel 工作表
    """
    print("=== Example 4: Load Excel (Specific Sheet) ===\n")
    
    # Configure to load specific sheet
    config = LoaderConfig(
        excel_sheet_name="Sheet1",
        excel_skip_rows=0
    )
    
    doc = load_document(
        "data/test/test_medical_records_multilang.xlsx",
        config=config
    )
    
    print(f"Loaded sheet: {config.excel_sheet_name}")
    print(f"Records: {len(doc.records)}")
    print()


def example_5_load_word_document():
    """
    Example 5: Load Word document
    範例 5：載入 Word 文件
    """
    print("=== Example 5: Load Word Document ===\n")
    
    # Load DOCX
    doc = load_document("data/test/medical_report.docx")
    
    print(f"File: {doc.metadata.filename}")
    print(f"Paragraphs: {doc.metadata.custom.get('num_paragraphs', 0)}")
    print(f"Tables: {doc.metadata.custom.get('num_tables', 0)}")
    print(f"Author: {doc.metadata.custom.get('author', 'N/A')}")
    
    print(f"\nContent preview:\n{doc.content[:300]}...")
    print()


def example_6_load_json_structured():
    """
    Example 6: Load JSON with structured data
    範例 6：載入 JSON（含結構化資料）
    """
    print("=== Example 6: Load JSON ===\n")
    
    # Load JSON
    doc = load_document("data/test/patient_record.json")
    
    print(f"File: {doc.metadata.filename}")
    print(f"\nStructured data keys:")
    if doc.structured_data:
        for key in doc.structured_data.keys():
            print(f"  - {key}")
        
        print(f"\nPatient ID: {doc.structured_data.get('patient_id', 'N/A')}")
    
    print()


def example_7_load_pdf():
    """
    Example 7: Load PDF file
    範例 7：載入 PDF 檔案
    """
    print("=== Example 7: Load PDF ===\n")
    
    # Configure PDF loading
    config = LoaderConfig(
        pdf_page_range=(1, 3)  # First 3 pages only
    )
    
    doc = load_document("data/test/lab_results.pdf", config=config)
    
    print(f"File: {doc.metadata.filename}")
    print(f"Pages extracted: {doc.metadata.custom.get('num_pages', 0)}")
    
    print(f"\nContent preview:\n{doc.content[:300]}...")
    print()


def example_8_load_html():
    """
    Example 8: Load HTML file
    範例 8：載入 HTML 檔案
    """
    print("=== Example 8: Load HTML ===\n")
    
    # Configure HTML loading
    config = LoaderConfig(
        html_extract_text_only=True,
        html_remove_scripts=True
    )
    
    doc = load_document("data/test/patient_portal.html", config=config)
    
    print(f"File: {doc.metadata.filename}")
    print(f"Title: {doc.metadata.custom.get('title', 'N/A')}")
    
    print(f"\nExtracted text:\n{doc.content[:300]}...")
    print()


def example_9_load_xml():
    """
    Example 9: Load XML file
    範例 9：載入 XML 檔案
    """
    print("=== Example 9: Load XML ===\n")
    
    doc = load_document("data/test/lab_data.xml")
    
    print(f"File: {doc.metadata.filename}")
    print(f"Root tag: {doc.metadata.custom.get('root_tag', 'N/A')}")
    
    print(f"\nStructured data:")
    if doc.structured_data:
        import json
        print(json.dumps(doc.structured_data, indent=2, ensure_ascii=False)[:500])
    
    print()


def example_10_load_fhir():
    """
    Example 10: Load FHIR resource
    範例 10：載入 FHIR 資源
    """
    print("=== Example 10: Load FHIR Resource ===\n")
    
    doc = load_document("data/test/patient_fhir.json")
    
    print(f"File: {doc.metadata.filename}")
    print(f"Resource Type: {doc.metadata.custom.get('fhir_resource_type', 'N/A')}")
    print(f"Resource ID: {doc.metadata.custom.get('fhir_resource_id', 'N/A')}")
    
    if doc.structured_data:
        print(f"\nPatient name: {doc.structured_data.get('name', 'N/A')}")
    
    print()


def example_11_load_directory():
    """
    Example 11: Load all documents from directory
    範例 11：從目錄載入所有文件
    """
    print("=== Example 11: Load Directory ===\n")
    
    # Load all Excel files
    docs = load_documents_from_directory(
        directory="data/test",
        pattern="*.xlsx",
        recursive=False
    )
    
    print(f"Loaded {len(docs)} Excel files:")
    for doc in docs:
        print(f"  - {doc.metadata.filename}: {len(doc.records)} records")
    
    print()


def example_12_load_directory_recursive():
    """
    Example 12: Load all documents recursively
    範例 12：遞迴載入所有文件
    """
    print("=== Example 12: Load Directory (Recursive) ===\n")
    
    # Load all supported files
    docs = load_documents_from_directory(
        directory="data/test",
        pattern="*",
        recursive=True
    )
    
    print(f"Loaded {len(docs)} documents")
    
    # Group by format
    format_counts = {}
    for doc in docs:
        fmt = doc.metadata.format.value
        format_counts[fmt] = format_counts.get(fmt, 0) + 1
    
    print("\nBy format:")
    for fmt, count in format_counts.items():
        print(f"  - {fmt}: {count}")
    
    print()


def example_13_batch_processing():
    """
    Example 13: Batch process multiple files
    範例 13：批次處理多個檔案
    """
    print("=== Example 13: Batch Processing ===\n")
    
    file_paths = [
        "data/test/test_medical_records_multilang.xlsx",
        "data/test/test_complex_phi_cases.xlsx",
    ]
    
    # Load all files
    from core.infrastructure.loader import DocumentLoaderFactory
    
    factory = DocumentLoaderFactory()
    docs = factory.load_multiple(file_paths)
    
    print(f"Processed {len(docs)} files:")
    for doc in docs:
        num_records = len(doc.records) if doc.records else 0
        print(f"  - {doc.metadata.filename}: {num_records} records")
    
    print()


def example_14_custom_config():
    """
    Example 14: Load with custom configuration
    範例 14：使用自訂配置載入
    """
    print("=== Example 14: Custom Configuration ===\n")
    
    # Create custom config
    config = LoaderConfig(
        encoding="utf-8",
        preserve_formatting=False,
        extract_metadata=True,
        max_file_size=10 * 1024 * 1024,  # 10 MB
        excel_skip_rows=1,  # Skip first row
        csv_delimiter=",",
        pdf_page_range=(1, 5)
    )
    
    print("Custom configuration:")
    print(f"  - Encoding: {config.encoding}")
    print(f"  - Max file size: {config.max_file_size} bytes")
    print(f"  - Excel skip rows: {config.excel_skip_rows}")
    
    # Use config
    doc = load_document("data/test/test_medical_records_multilang.xlsx", config=config)
    
    print(f"\nLoaded: {doc.metadata.filename}")
    print(f"Records: {len(doc.records)}")
    print()


def example_15_error_handling():
    """
    Example 15: Error handling
    範例 15：錯誤處理
    """
    print("=== Example 15: Error Handling ===\n")
    
    # Try to load non-existent file
    try:
        doc = load_document("nonexistent.txt")
    except FileNotFoundError as e:
        print(f"✗ FileNotFoundError: {e}")
    
    # Try to load unsupported format
    try:
        doc = load_document("data/test/unsupported.xyz")
    except ValueError as e:
        print(f"✗ ValueError: {e}")
    
    print("\n✓ Error handling works correctly")
    print()


def example_16_get_supported_formats():
    """
    Example 16: Get supported formats
    範例 16：取得支援的格式
    """
    print("=== Example 16: Supported Formats ===\n")
    
    formats = get_supported_formats()
    
    print(f"Supported formats ({len(formats)}):")
    for fmt in formats:
        print(f"  - .{fmt}")
    
    print()


def example_17_loader_factory():
    """
    Example 17: Using DocumentLoaderFactory
    範例 17：使用 DocumentLoaderFactory
    """
    print("=== Example 17: DocumentLoaderFactory ===\n")
    
    from core.infrastructure.loader import DocumentLoaderFactory
    
    factory = DocumentLoaderFactory()
    
    # Create loader for specific format
    loader = factory.create_loader("data/test/test_medical_records_multilang.xlsx")
    print(f"Created loader: {loader}")
    
    # Load document
    doc = loader.load("data/test/test_medical_records_multilang.xlsx")
    print(f"Loaded: {doc.metadata.filename}")
    print(f"Records: {len(doc.records)}")
    print()


def example_18_integration_with_rag():
    """
    Example 18: Integration with RAG system
    範例 18：與 RAG 系統整合
    """
    print("=== Example 18: Integration with RAG ===\n")
    
    # Load medical document
    doc = load_document("data/test/test_medical_records_multilang.xlsx")
    
    print(f"Loaded: {doc.metadata.filename}")
    print(f"Records: {len(doc.records)}")
    
    # Prepare for RAG processing
    if doc.records:
        print("\nReady for RAG-based PHI identification:")
        
        # Example: Take first 3 records
        for i, record in enumerate(doc.records[:3], 1):
            # Get clinical summary (contains PHI)
            clinical_summary = record.get("Clinical Summary", "")
            
            print(f"\nRecord {i}:")
            print(f"  Length: {len(clinical_summary)} chars")
            print(f"  Preview: {clinical_summary[:100]}...")
            
            # This text would be sent to RAG chain for PHI identification
            # chain.identify_phi(clinical_summary, language="zh-TW")
    
    print()


def main():
    """Run all examples"""
    examples = [
        example_1_load_text_file,
        example_2_load_csv_file,
        example_3_load_excel_all_sheets,
        example_4_load_excel_specific_sheet,
        example_5_load_word_document,
        example_6_load_json_structured,
        example_7_load_pdf,
        example_8_load_html,
        example_9_load_xml,
        example_10_load_fhir,
        example_11_load_directory,
        example_12_load_directory_recursive,
        example_13_batch_processing,
        example_14_custom_config,
        example_15_error_handling,
        example_16_get_supported_formats,
        example_17_loader_factory,
        example_18_integration_with_rag,
    ]
    
    print("=" * 60)
    print("Document Loader Usage Examples")
    print("=" * 60)
    print()
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        try:
            example()
        except Exception as e:
            print(f"✗ Example {i} failed: {e}\n")
        
        if i < len(examples):
            input("Press Enter to continue to next example...")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run specific example
    import sys
    
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_1_load_text_file,
            example_2_load_csv_file,
            example_3_load_excel_all_sheets,
            example_4_load_excel_specific_sheet,
            example_5_load_word_document,
            example_6_load_json_structured,
            example_7_load_pdf,
            example_8_load_html,
            example_9_load_xml,
            example_10_load_fhir,
            example_11_load_directory,
            example_12_load_directory_recursive,
            example_13_batch_processing,
            example_14_custom_config,
            example_15_error_handling,
            example_16_get_supported_formats,
            example_17_loader_factory,
            example_18_integration_with_rag,
        ]
        
        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        # Run first few examples for quick demo
        print("Running quick demo (first 3 examples)...\n")
        example_1_load_text_file()
        example_3_load_excel_all_sheets()
        example_16_get_supported_formats()
