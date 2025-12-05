# 🏗️ Architecture Guide | 架構指南

## Overview | 概述

Medical De-identification Toolkit follows **Domain-Driven Design (DDD)** principles with a clean **layered architecture**. This document explains the system design and component interactions.

本工具套件遵循 **領域驅動設計 (DDD)** 原則，採用清晰的 **分層架構**。本文檔說明系統設計與組件互動。

---

## 📐 Layered Architecture | 分層架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         Interface Layer                          │
│                    (CLI, API, Web UI - Future)                   │
├─────────────────────────────────────────────────────────────────┤
│                        Application Layer                         │
│            (Use Cases, Orchestration, Batch Processing)          │
├─────────────────────────────────────────────────────────────────┤
│                       Infrastructure Layer                       │
│          (LLM, RAG, Document Loaders, Output, Utils)            │
├─────────────────────────────────────────────────────────────────┤
│                          Domain Layer                            │
│        (Entities, Value Objects, Domain Services, Types)         │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities | 各層職責

| Layer | Responsibility | Dependencies |
|-------|----------------|--------------|
| **Domain** | Business logic, types, entities | None (pure Python) |
| **Infrastructure** | Technical implementations | Domain |
| **Application** | Use case orchestration | Domain, Infrastructure |
| **Interface** | User interaction | Application |

---

## 📁 Project Structure | 專案結構

```
medical_deidentification/
├── domain/                          # 🎯 Domain Layer
│   ├── __init__.py
│   ├── phi_types.py                 # PHI type definitions (PHIType enum)
│   ├── masking_types.py             # Masking strategy types (StrategyType)
│   ├── entities.py                  # PHIEntity, PHIMatch
│   ├── value_objects.py             # DocumentMetadata, ProcessingResult
│   ├── configs.py                   # DeidentificationConfig
│   ├── aggregates.py                # MedicalDocument (Aggregate Root)
│   └── phi_type_mapper.py           # PHI type mapping utilities
│
├── application/                     # ⚙️ Application Layer
│   ├── __init__.py
│   └── processing/
│       ├── __init__.py
│       ├── batch_processor.py       # BatchPHIProcessor
│       ├── pipeline.py              # DeidentificationPipeline
│       ├── strategies.py            # Strategy implementations
│       ├── context.py               # Processing context
│       ├── output_manager.py        # Re-export (→ infrastructure)
│       ├── report_generator.py      # Re-export (→ infrastructure)
│       └── engine/
│           ├── __init__.py
│           ├── core.py              # DeidentificationEngine
│           ├── config.py            # EngineConfig
│           ├── masking.py           # MaskingService
│           └── handlers.py          # PHI handlers
│
├── infrastructure/                  # 🔧 Infrastructure Layer
│   ├── __init__.py
│   ├── llm/                         # LLM Integration
│   │   ├── __init__.py
│   │   ├── config.py                # LLMConfig, LLMPresets
│   │   ├── factory.py               # create_llm(), factory functions
│   │   └── manager.py               # LLM manager utilities
│   │
│   ├── rag/                         # RAG Engine
│   │   ├── __init__.py
│   │   ├── embeddings.py            # EmbeddingsManager
│   │   ├── regulation_store.py      # RegulationVectorStore
│   │   ├── regulation_retriever.py  # RegulationRetriever (MMR)
│   │   ├── regulation_retrieval_chain.py  # RegulationRetrievalChain
│   │   ├── phi_identification_chain.py    # PHIIdentificationChain
│   │   ├── medical_retriever.py     # MedicalTextRetriever
│   │   └── text_splitter.py         # Text splitting utilities
│   │
│   ├── loader/                      # Document Loaders
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseLoader, LoadedDocument
│   │   ├── loaders.py               # Format-specific loaders
│   │   └── factory.py               # DocumentLoaderFactory
│   │
│   ├── output/                      # Output Management
│   │   ├── __init__.py
│   │   ├── output_manager.py        # OutputManager
│   │   └── report_generator.py      # ReportGenerator
│   │
│   ├── prompts/                     # Prompt Templates
│   │   ├── __init__.py
│   │   └── templates.py             # PHI identification prompts
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       └── logging.py               # Logging configuration
│
├── interface/                       # 🖥️ Interface Layer
│   └── __init__.py                  # (CLI/API - Future)
│
└── __init__.py                      # Package exports
```

---

## 🎯 Domain Layer | 領域層

The domain layer contains **pure business logic** with no external dependencies.

### Core Types | 核心類型

```python
# domain/phi_types.py
class PHIType(str, Enum):
    """Protected Health Information types | PHI 類型"""
    NAME = "NAME"                      # 姓名
    DATE = "DATE"                      # 日期
    LOCATION = "LOCATION"              # 地點
    AGE_OVER_89 = "AGE_OVER_89"       # 年齡 > 89
    MEDICAL_RECORD_NUMBER = "MEDICAL_RECORD_NUMBER"
    PHONE = "PHONE"                    # 電話
    EMAIL = "EMAIL"                    # 電子郵件
    ID_NUMBER = "ID_NUMBER"            # 身分證號
    RARE_DISEASE = "RARE_DISEASE"      # 罕見疾病
    # ... 20+ types

# domain/masking_types.py
class StrategyType(str, Enum):
    """Masking strategy types | 遮蔽策略類型"""
    REDACTION = "redaction"            # 完全刪除
    GENERALIZATION = "generalization"  # 泛化
    PSEUDONYMIZATION = "pseudonymization"  # 假名化
    DATE_SHIFTING = "date_shifting"    # 日期偏移
    PARTIAL_MASKING = "partial_masking"  # 部分遮蔽
    SUPPRESSION = "suppression"        # 抑制
```

### Entities | 實體

```python
# domain/entities.py
@dataclass
class PHIEntity:
    """Identified PHI entity | 識別的 PHI 實體"""
    text: str                   # Original text
    phi_type: PHIType           # PHI category
    start_pos: int              # Start position
    end_pos: int                # End position
    confidence: float           # Detection confidence (0-1)
    reason: Optional[str]       # Detection reason
    regulation_source: Optional[str]  # Source regulation
```

---

## 🔧 Infrastructure Layer | 基礎設施層

Technical implementations that can be swapped without affecting business logic.

### LLM Integration | LLM 整合

```python
# infrastructure/llm/config.py
class LLMConfig(BaseModel):
    provider: Literal["openai", "anthropic", "ollama"]
    model_name: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    use_gpu: bool = True

# infrastructure/llm/factory.py
def create_llm(config: LLMConfig) -> BaseChatModel:
    """Factory for creating LLM instances"""
    if config.provider == "openai":
        return _create_openai_llm(config)
    elif config.provider == "anthropic":
        return _create_anthropic_llm(config)
    elif config.provider == "ollama":
        return _create_ollama_llm(config)
```

### Supported LLM Providers | 支援的 LLM

| Provider | Package | Models |
|----------|---------|--------|
| OpenAI | `langchain-openai` | GPT-4o, GPT-4o-mini, GPT-3.5 |
| Anthropic | `langchain-anthropic` | Claude 3 Opus/Sonnet/Haiku |
| Ollama | `langchain-ollama` | Qwen, Llama, Mistral, **MiniMind** |

### RAG Engine | RAG 引擎

```python
# infrastructure/rag/phi_identification_chain.py
class PHIIdentificationChain:
    """Main PHI identification using LLM + RAG"""
    
    def identify_phi(
        self, 
        text: str, 
        language: str = "zh-TW"
    ) -> List[PHIEntity]:
        # 1. Retrieve relevant regulations
        regulations = self.regulation_chain.retrieve(text)
        
        # 2. Build prompt with context
        prompt = self._build_prompt(text, regulations, language)
        
        # 3. Call LLM for identification
        response = self.llm.invoke(prompt)
        
        # 4. Parse and validate results
        entities = self._parse_response(response)
        return entities
```

### Document Loaders | 文件載入器

| Format | Loader | Features |
|--------|--------|----------|
| TXT | `TextLoader` | Encoding detection |
| CSV | `CSVLoader` | Header support, delimiter config |
| XLSX/XLS | `ExcelLoader` | Multi-sheet, openpyxl/xlrd |
| DOCX | `WordLoader` | python-docx |
| PDF | `PDFLoader` | pdfplumber, page ranges |
| JSON | `JSONLoader` | Structured data preservation |
| HTML | `HTMLLoader` | BeautifulSoup, script removal |
| XML | `XMLLoader` | Dict conversion |
| FHIR | `FHIRLoader` | FHIR R4 JSON validation |

---

## ⚙️ Application Layer | 應用層

Use case orchestration and business workflows.

### Batch Processing | 批次處理

```python
# application/processing/batch_processor.py
class BatchPHIProcessor:
    """Process multiple documents in batch"""
    
    def process_excel_file(
        self,
        file_path: str,
        case_id_column: Optional[str] = None
    ) -> BatchProcessingResult:
        # 1. Load Excel file
        df = pd.read_excel(file_path)
        
        # 2. Process each row
        results = []
        for idx, row in df.iterrows():
            text = self._combine_columns(row)
            entities = self.phi_chain.identify_phi(text)
            results.append(RowProcessingResult(...))
        
        # 3. Aggregate results
        return BatchProcessingResult(
            file_name=file_path,
            row_results=results,
            total_entities=sum(len(r.entities) for r in results)
        )
```

### De-identification Engine | 去識別化引擎

```python
# application/processing/engine/core.py
class DeidentificationEngine:
    """Main engine for de-identification"""
    
    def process(self, text: str) -> ProcessingResult:
        # 1. Identify PHI entities
        entities = self.phi_chain.identify_phi(text)
        
        # 2. Apply masking strategies
        masked_text = self.masking_service.apply(text, entities)
        
        # 3. Generate report
        report = self.report_generator.generate(entities)
        
        return ProcessingResult(
            original_text=text,
            deidentified_text=masked_text,
            entities=entities,
            report=report
        )
```

---

## 🔄 Data Flow | 資料流程

```
┌──────────────┐
│   Input      │  Excel, PDF, TXT, etc.
│  Document    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Document Loader (Infrastructure)    │
│  - Parse format                      │
│  - Extract text & metadata           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  RAG Regulation Engine               │◄──── Regulation Vector Store
│  - Retrieve applicable rules         │      (HIPAA, GDPR, PDPA)
│  - Generate masking instructions     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  PHI Identification Chain            │
│  ┌────────────────────────────────┐  │
│  │ LLM (OpenAI/Anthropic/Ollama)  │  │
│  │ - Detect PHI entities          │  │
│  │ - Classify PHI types           │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Masking Service (Application)       │
│  - Apply de-identification strategy  │
│  - Redaction / Generalization / etc. │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Output Manager (Infrastructure)     │
│  - Format results (JSON, Excel)      │
│  - Generate reports                  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│ De-identified│
│   Document   │
└──────────────┘
```

---

## 🔐 Privacy Design | 隱私設計

### Key Principles | 關鍵原則

1. **In-Memory Processing**: Medical data is **never persisted** to disk
2. **Regulation Persistence**: Only public regulation documents are stored in vector DB
3. **No PHI in Logs**: Logging excludes actual PHI content
4. **Ephemeral Vector Store**: Document vectors are destroyed after processing

```python
# Privacy-safe design
class MedicalTextRetriever:
    def process(self, text: str) -> List[PHIEntity]:
        # Create temporary in-memory vector store
        temp_store = FAISS.from_texts([text], self.embeddings)
        
        try:
            # Process document
            result = self._identify_phi(temp_store)
            return result
        finally:
            # Always destroy temporary store
            del temp_store
```

---

## 🧪 Testing Strategy | 測試策略

```
tests/
├── unit/                    # Unit tests (isolated)
│   ├── domain/              # Domain layer tests
│   ├── infrastructure/      # Infrastructure tests
│   └── application/         # Application tests
├── integration/             # Integration tests
│   ├── test_llm_integration.py
│   └── test_rag_chain.py
└── e2e/                     # End-to-end tests
    └── test_full_pipeline.py
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=medical_deidentification --cov-report=html

# Run specific layer
pytest tests/unit/domain/
```

---

## 📈 Design Patterns | 設計模式

| Pattern | Usage | Example |
|---------|-------|---------|
| **Factory** | LLM creation | `create_llm(config)` |
| **Strategy** | De-identification methods | `RedactionStrategy`, `GeneralizationStrategy` |
| **Chain of Responsibility** | Processing pipeline | `PHIIdentificationChain` |
| **Repository** | Document storage | `RegulationVectorStore` |
| **Observer** | Progress tracking | `BatchProcessingResult` |

---

## 🔮 Future Enhancements | 未來增強

- [ ] REST API interface (FastAPI)
- [ ] Web UI for interactive use
- [ ] Streaming output support
- [ ] Parallel batch processing
- [ ] Custom PHI type definitions via UI
- [ ] Compliance validation module

---

<div align="center">

**[← Back to README](../README.md)**

</div>
