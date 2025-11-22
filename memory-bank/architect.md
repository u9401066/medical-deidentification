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

```
┌─────────────────────────────────────────┐
│      MedicalDocument (Aggregate)        │
├─────────────────────────────────────────┤
│ - id: DocumentId                        │
│ - originalText: str                     │
│ - detectedEntities: List[PHIEntity]     │
│ - deidentifiedText: str                 │
│ - metadata: DocumentMetadata            │
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

