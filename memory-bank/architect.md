# Medical Text De-identification Toolkit: System Architect | 系統架構

## Overview | 概述

This document outlines the architectural design for the Medical Text De-identification Toolkit, following Domain-Driven Design (DDD) principles and MVP development methodology.

本文件概述醫療文本去識別化工具套件的架構設計,遵循領域驅動設計 (DDD) 原則與 MVP 開發方法論。

## Architectural Decisions | 架構決策

### 1. Domain-Driven Design (DDD) Architecture | 領域驅動設計架構

**Decision**: Adopt DDD with clear bounded contexts and rich domain models.

**Rationale**: 
- Medical de-identification is a complex domain with specific rules and regulations
- 醫療去識別化是具有特定規則與法規的複雜領域
- Clear separation of concerns improves maintainability
- 清晰的關注點分離提升可維護性
- Ubiquitous language ensures team alignment
- 統一語言確保團隊一致性

### 2. Layered Architecture | 分層架構

**Decision**: Implement a clean layered architecture.

**Rationale**:
- Domain Layer: Pure business logic, framework-agnostic
- Application Layer: Use cases and orchestration
- Infrastructure Layer: External integrations (LLM, file I/O)
- Interface Layer: CLI, API endpoints

### 3. Strategy Pattern for De-identification | 策略模式用於去識別化

**Decision**: Use Strategy pattern for flexible de-identification methods.

**Rationale**:
- Allows runtime selection of de-identification strategies
- 允許運行時選擇去識別化策略
- Easy to extend with new strategies
- 易於擴展新策略
- Supports user-defined custom strategies
- 支援用戶自定義策略

### 4. Async Processing for Batch Operations | 非同步處理批次操作

**Decision**: Use asyncio for batch processing.

**Rationale**:
- Improves throughput for I/O-bound LLM API calls
- 提升 I/O 密集的 LLM API 呼叫吞吐量
- Better resource utilization
- Supports concurrent processing
- 支援並行處理

### 5. RAG-based Regulation Retrieval | 基於 RAG 的規範檢索

**Decision**: Implement RAG (Retrieval-Augmented Generation) to retrieve relevant de-identification regulations and guidelines.

**Rationale**:
- Dynamically retrieve applicable PHI detection rules from regulation documents
- 動態檢索適用的個資檢測規則
- Generate precise masking instructions while preserving unaffected content
- 生成精準的遮蔽指令,同時保留不受影響的內容
- Enable context-aware de-identification based on regulatory requirements
- 基於法規要求進行上下文感知的去識別化
- Maintain regulation knowledge base separate from code logic
- 將法規知識庫與程式邏輯分離

## Core Module Architecture | 核心模組架構

The system is organized into **6 core modules** aligned with DDD principles:

本系統組織為 **6 個核心模組**,符合 DDD 原則:

### Module 1: Document Loader | 文本載入模組
**Purpose**: Handle various input formats and document structures
**Status**: ✅ Implementation Complete | 實作完成

**Implemented Files**:
- `infrastructure/loader/base.py` (400 lines) - Abstract base classes and data models
- `infrastructure/loader/loaders.py` (750 lines) - 10 format-specific loaders
- `infrastructure/loader/factory.py` (320 lines) - Factory pattern and utilities
- `infrastructure/loader/__init__.py` - Module exports
- `examples/loader_usage_examples.py` (550 lines) - 18 usage scenarios

**Supported Formats**:
- TXT: Plain text files with encoding detection
- CSV: Comma-separated values with header support
- XLSX: Excel 2007+ with multi-sheet support (openpyxl)
- XLS: Excel legacy format (xlrd)
- DOCX: Microsoft Word documents (python-docx)
- JSON: Structured JSON with data preservation
- PDF: Portable Document Format (pdfplumber/PyPDF2)
- HTML: Web documents with text extraction (BeautifulSoup)
- XML: Structured XML with dict conversion
- FHIR: Healthcare interoperability standard (FHIR R4 JSON)

**Key Features**:
- Automatic format detection from file extension
- Metadata extraction (filename, size, dates, encoding)
- Multi-sheet Excel support with sheet selection
- CSV with header/delimiter configuration
- PDF page range extraction
- HTML text-only extraction with script removal
- XML to dictionary conversion
- FHIR resource validation
- Batch loading from directories (recursive support)
- Error handling with detailed logging
- Factory pattern for loader creation
- Unified LoadedDocument return format

**Architecture**:
```python
DocumentLoader (ABC)
  ├── BaseTextLoader
  │     ├── TextLoader
  │     ├── CSVLoader
  │     ├── JSONLoader
  │     ├── HTMLLoader
  │     ├── XMLLoader
  │     └── FHIRLoader (extends JSONLoader)
  └── BaseBinaryLoader
        ├── ExcelLoader (XLSX/XLS)
        ├── WordLoader (DOCX)
        └── PDFLoader

DocumentLoaderFactory
  ├── create_loader() - Factory method
  ├── load() - Convenience method
  └── load_directory() - Batch loading
```

**Data Models**:
- `DocumentFormat`: Enum of supported formats
- `DocumentMetadata`: File metadata (path, size, dates, encoding, custom)
- `LoadedDocument`: Unified document with content + metadata + structured_data + records
- `LoaderConfig`: Configuration (encoding, Excel sheets, CSV delimiter, PDF pages)

**Usage Example**:
```python
from medical_deidentification.infrastructure.loader import load_document

# Simple loading
doc = load_document("patient_records.xlsx")

# Access content
print(doc.content)  # Text representation

# Access structured data
print(doc.records[0])  # First record as dict

# Access metadata
print(doc.metadata.filename)
print(doc.metadata.file_size)
```

- Support multiple formats (TXT, JSON, CSV, FHIR)
- 支援多種格式
- Normalize document structure for processing
- 標準化文件結構
- Extract metadata and context
- 提取元數據與上下文

### Module 2: RAG Regulation Engine | RAG 規範引擎 (創新核心)
**Purpose**: Retrieve relevant de-identification rules using RAG
**Status**: ✅ Core Implementation Complete | 核心實作完成
**技術選型**: LangChain + In-Memory Vector Store (無持久化病歷)

**Implemented Files**:
- `infrastructure/rag/embeddings.py` (190 lines) - EmbeddingsManager with multilingual presets
- `infrastructure/rag/regulation_store.py` (470 lines) - RegulationVectorStore + InMemoryDocumentProcessor
- `infrastructure/rag/retriever.py` (350 lines) - RegulationRetriever with MMR
- `infrastructure/rag/regulation_chain.py` (450 lines) - RegulationRAGChain with LLM
- `examples/rag_usage_examples.py` (450 lines) - 8 usage scenarios
- `docs/RAG_USAGE_GUIDE.md` (600+ lines) - Comprehensive documentation

#### 核心概念
- **Key Innovation**: RAG retrieves "what to mask" not "what to preserve"
- **關鍵創新**: RAG 檢索「要遮蔽什麼」而非「要保留什麼」
- Traditional RAG: 檢索相關知識來回答問題
- This system RAG: 檢索法規定義的「個資類型」來指導遮罩
- Advantage: 彈性支援不同國家/地區法規（HIPAA, GDPR, PDPA, 台灣個資法）

#### 為何選擇 LangChain？
1. **統一管理介面**: LLM / RAG / Agent 三合一
2. **多 Provider 支援**: OpenAI, Anthropic, Azure OpenAI, 本地模型（Ollama, HuggingFace）
3. **豐富生態系統**: Document Loaders, Text Splitters, Retrievers, Chains
4. **成熟穩定**: 廣泛使用，文檔完善，社群活躍

#### 隱私設計原則
- ❌ **不持久化病歷文本向量** - 避免個資外洩
- ✅ **可持久化法規文本向量** - 法規是公開資訊
- ✅ **In-memory 處理病歷** - 處理完即銷毀

#### 技術架構
```python
# Regulation Vector Store (Persistent) - 法規可持久化
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# 法規文件結構
regulations/
  ├── vectorstore/              # FAISS 持久化向量庫
  │   ├── index.faiss
  │   └── index.pkl
  ├── source_documents/         # 原始法規文件
  │   ├── hipaa_safe_harbor.md
  │   ├── taiwan_personal_data_law.md
  │   ├── gdpr_article_4.md
  │   └── custom_phi_definitions.md
  └── metadata.json

# RAG Pipeline 組件
class RegulationRAG:
    - embeddings: HuggingFaceEmbeddings (本地模型)
    - regulation_store: FAISS (persistent)
    - retriever: MMR (Maximal Marginal Relevance)
    - llm_chain: LangChain RetrievalQA
    
    methods:
    - retrieve_phi_types(context, strictness) -> List[PHIType]
    - query_age_handling(age) -> str
    - query_rare_disease() -> str
    - query_geographic_rules(location) -> str

# Medical Document Processing (Ephemeral) - 病歷不持久化
def process_medical_document(doc_text: str):
    # 建立臨時 in-memory vector store
    temp_vectorstore = FAISS.from_texts(texts, embeddings)
    
    # 處理後立即銷毀
    result = deidentify_with_rag(temp_vectorstore, regulation_store)
    del temp_vectorstore
    return result
```

#### RAG Integration with LLM
- Semantic search for applicable PHI detection rules
- 語義搜尋適用的個資檢測規則
- Generate context-specific masking instructions
- 生成上下文特定的遮蔽指令
- LangChain RetrievalQA chain for regulation queries
- Prompt engineering for PHI extraction
- Return structured PHI entities with confidence scores

### Module 3: Core Processing Engine | 核心處理引擎
**Purpose**: Orchestrate the de-identification workflow
- PHI detection using LLM + RAG-retrieved rules
- 使用 LLM + RAG 檢索規則進行個資檢測
- Apply de-identification strategies
- 應用去識別化策略
- Maintain processing context and state
- 維護處理上下文與狀態

### Module 4: LLM Integration Layer | LLM 串接層
**Purpose**: Abstract and manage LLM provider interactions
- Provider abstraction (OpenAI, Anthropic, local models)
- 提供者抽象化
- Prompt engineering and management
- 提示詞工程與管理
- Response parsing and validation
- 回應解析與驗證
- Rate limiting and retry logic
- 速率限制與重試邏輯

### Module 5: Output Module | 輸出模組
**Purpose**: Format and export de-identified results
- Multiple output formats (JSON, CSV, TXT, FHIR)
- 多種輸出格式
- Generate audit logs and reports
- 生成審計日誌與報告
- Maintain original-to-deidentified mapping (optional, encrypted)
- 維護原始到去識別化的映射（可選,加密）

### Module 6: Validation & Quality Assurance | 檢核模組
**Purpose**: Ensure de-identification quality and completeness
- Verify no PHI remains in output
- 驗證輸出中無殘留個資
- Calculate quality metrics (precision, recall, F1)
- 計算品質指標
- Compliance checking against regulations
- 法規合規性檢查
- Generate validation reports
- 生成驗證報告

## System Components | 系統組件

### 1. De-identification Context | 去識別化上下文

**Responsibilities | 職責**:
- Define PHI entities and detection rules
- 定義個人健康資訊實體與檢測規則
- Execute de-identification strategies
- 執行去識別化策略
- Validate de-identification completeness
- 驗證去識別化完整性

**Key Aggregates | 關鍵聚合**:
- `MedicalDocument` (Aggregate Root)
  - Contains original text, detected PHI entities, de-identified text
  - 包含原始文本、檢測到的個資實體、去識別化文本
- `PHIEntity` (Value Object)
  - Type (name, date, location, ID, etc.)
  - Position in text
  - Confidence score

**Key Services | 關鍵服務**:
- `PHIDetectionService`: Orchestrates PHI detection
- `DeidentificationService`: Applies strategies
- `ValidationService`: Validates results

### 2. LLM Integration Context | LLM 整合上下文

**Responsibilities | 職責**:
- Abstract LLM provider differences
- 抽象化不同 LLM 提供者的差異
- Handle API calls and retries
- 處理 API 呼叫與重試
- Manage prompts and responses
- 管理提示詞與回應

**Key Components | 關鍵組件**:
- `LLMProvider` (Interface)
  - `OpenAIProvider`
  - `AnthropicProvider`
  - `LocalModelProvider`
- `PromptTemplate`: Structured prompts for PHI detection
- `ResponseParser`: Parse LLM responses into structured data

### 3. Batch Processing Context | 批次處理上下文

**Responsibilities | 職責**:
- Manage batch job lifecycle
- 管理批次作業生命週期
- Progress tracking and reporting
- 進度追蹤與報告
- Error handling and recovery
- 錯誤處理與恢復

**Key Components | 關鍵組件**:
- `BatchProcessor`: Main orchestrator
- `JobQueue`: Manages processing queue
- `ProgressTracker`: Real-time progress updates
- `ResultCollector`: Aggregates results

### 4. Validation Context | 驗證上下文

**Responsibilities | 職責**:
- Quality metrics calculation
- 品質指標計算
- False positive/negative detection
- 誤檢/漏檢偵測
- Compliance checking
- 合規性檢查

**Key Components | 關鍵組件**:
- `MetricsCalculator`: Precision, recall, F1-score
- `ComplianceValidator`: HIPAA/GDPR rules
- `QualityReporter`: Generate quality reports

## Domain Model | 領域模型

### Enhanced Domain Model with RAG Integration

```
┌─────────────────────────────────────────────────┐
│      MedicalDocument (Aggregate Root)           │
├─────────────────────────────────────────────────┤
│ - id: DocumentId                                │
│ - originalText: str                             │
│ - detectedEntities: List[PHIEntity]             │
│ - deidentifiedText: str                         │
│ - metadata: DocumentMetadata                    │
│ - regulationContext: RegulationContext          │
├─────────────────────────────────────────────────┤
│ + loadDocument(loader: DocumentLoader)          │
│ + detectPHI(detector: PHIDetector, rag: RAG)    │
│ + applyStrategy(strategy: Strategy)             │
│ + validate(validator: Validator): ValidationResult│
│ + export(exporter: OutputExporter)              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│       PHIEntity (Value Object)                  │
├─────────────────────────────────────────────────┤
│ - type: PHIType (NAME, DATE, LOCATION, etc.)   │
│ - text: str                                     │
│ - startPos: int                                 │
│ - endPos: int                                   │
│ - confidence: float                             │
│ - regulationSource: str (which rule detected it)│
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  RegulationContext (Value Object) - NEW         │
├─────────────────────────────────────────────────┤
│ - applicableRegulations: List[str]              │
│ - retrievedRules: List[RegulationRule]          │
│ - maskingInstructions: List[MaskingInstruction] │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  DeidentificationStrategy (Interface)           │
├─────────────────────────────────────────────────┤
│ + apply(entity: PHIEntity, context: str) -> str │
└─────────────────────────────────────────────────┘
         ▲
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
Redaction  Masking  Generalization Custom  RAGGuided
 遮蔽      遮罩       泛化        自定義   RAG引導
```

### Module Interaction Flow | 模組互動流程

```
┌──────────────┐
│   Input      │
│  Document    │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Module 1: Document Loader           │
│  - Parse format                      │
│  - Extract text & metadata           │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Module 2: RAG Regulation Engine     │◄──── Vector DB
│  - Query regulation knowledge base   │      (HIPAA, GDPR)
│  - Retrieve masking rules            │
│  - Generate context instructions     │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Module 3: Core Processing Engine    │
│  ┌────────────────────────────────┐  │
│  │ Module 4: LLM Integration      │  │
│  │ - Send text + RAG instructions │  │
│  │ - Detect PHI entities          │  │
│  └────────────────────────────────┘  │
│  - Apply de-identification strategy  │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Module 6: Validation Module         │
│  - Check for remaining PHI           │
│  - Calculate quality metrics         │
│  - Verify compliance                 │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Module 5: Output Module             │
│  - Format results                    │
│  - Generate reports                  │
│  - Export in desired format          │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────┐
│ De-identified│
│   Document   │
└──────────────┘
```
├─────────────────────────────────────────┤
│ + detectPHI(detector: PHIDetector)      │
│ + applyStrategy(strategy: Strategy)     │
│ + validate(): ValidationResult          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│       PHIEntity (Value Object)          │
├─────────────────────────────────────────┤
│ - type: PHIType                         │
│ - text: str                             │
│ - startPos: int                         │
│ - endPos: int                           │
│ - confidence: float                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  DeidentificationStrategy (Interface)   │
├─────────────────────────────────────────┤
│ + apply(entity: PHIEntity) -> str       │
└─────────────────────────────────────────┘
         ▲
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
Redaction  Masking  Generalization Custom
```

## Technology Stack Decisions | 技術堆疊決策

### Core Framework
- **Python 3.11+**: Modern async support, type hints
- **Pydantic v2**: Data validation and domain modeling
- **Poetry**: Dependency management

### LLM Integration
- **LangChain**: Flexible LLM abstraction layer
- 靈活的 LLM 抽象層
- Supports multiple providers out-of-the-box
- 原生支援多種提供者

### CLI Interface
- **Typer**: Modern CLI framework
- **Rich**: Beautiful terminal output with progress bars
- 美觀的終端輸出與進度條

## Deployment Architecture | 部署架構

### MVP Phase
- **Distribution**: PyPI package
- **Usage**: Command-line tool + Python library
- **Configuration**: YAML/JSON config files

### Future Considerations
- Docker containerization
- REST API service
- Web UI for interactive use

## Design Patterns Applied | 應用的設計模式

1. **Strategy Pattern**: De-identification strategies
2. **Factory Pattern**: LLM provider creation
3. **Repository Pattern**: Document storage/retrieval
4. **Observer Pattern**: Progress tracking
5. **Chain of Responsibility**: Processing pipeline
6. **Template Method**: Batch processing workflow

## Security Considerations | 安全考量

- No persistence of original medical data by default
- 預設不持久化原始醫療資料
- API keys stored in environment variables
- API 金鑰存於環境變數
- Audit logging for compliance
- 合規性審計日誌
- Optional encryption for intermediate results
- 中間結果可選加密

