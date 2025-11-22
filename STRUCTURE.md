# Project Structure | 專案結構

```
medical-deidentification/
├── medical_deidentification/           # Main package | 主要套件
│   ├── __init__.py
│   ├── domain/                        # Domain Layer | 領域層
│   │   ├── __init__.py
│   │   └── models.py                  # Domain models (Aggregates, Value Objects)
│   ├── application/                   # Application Layer | 應用層
│   │   └── __init__.py
│   ├── infrastructure/                # Infrastructure Layer | 基礎設施層
│   │   ├── __init__.py
│   │   ├── loader/                    # Module 1: Document Loader
│   │   ├── rag/                       # Module 2: RAG Regulation Engine ⭐
│   │   ├── llm/                       # Module 4: LLM Integration
│   │   ├── output/                    # Module 5: Output Module
│   │   └── validation/                # Module 6: Validation Module
│   └── interface/                     # Interface Layer | 介面層
│       └── __init__.py
├── tests/                             # Test suite | 測試套件
│   ├── conftest.py                    # Shared test fixtures
│   ├── unit/                          # Unit tests | 單元測試
│   ├── integration/                   # Integration tests | 整合測試
│   └── e2e/                           # End-to-end tests | 端到端測試
├── data/                              # Data directory | 資料目錄
│   ├── raw/                           # Raw medical data (never commit real PHI!)
│   ├── test/                          # Test data (synthetic only)
│   └── regulations/                   # Regulation documents for RAG
├── memory-bank/                       # Memory Bank | 記憶庫
│   ├── architect.md                   # System architecture
│   ├── projectBrief.md                # Project overview
│   ├── productContext.md              # Technical context
│   ├── systemPatterns.md              # Design patterns
│   ├── decisionLog.md                 # Decision log
│   └── progress.md                    # Progress tracking
├── pyproject.toml                     # Poetry configuration
├── README.md                          # Project README
└── .gitignore                         # Git ignore rules
```

## Module Organization | 模組組織

### Domain Layer (領域層)
Pure business logic, no external dependencies.
- `models.py`: Core domain models

### Application Layer (應用層)
Use cases and application services.
- Pipeline orchestration
- Use case implementations

### Infrastructure Layer (基礎設施層)
External integrations and technical implementations.

**Module 1: Document Loader**
- Format adapters (TXT, JSON, CSV, FHIR)
- Text extraction and normalization

**Module 2: RAG Regulation Engine** ⭐ 創新核心
- Vector database management
- Regulation retrieval
- Masking instruction generation

**Module 3: Core Processing Engine**
- Implemented in Application Layer
- Orchestrates all modules

**Module 4: LLM Integration**
- LLM provider abstractions
- Prompt management
- Response parsing

**Module 5: Output Module**
- Format exporters
- Report generators
- Audit logging

**Module 6: Validation Module**
- Quality metrics calculation
- Compliance checking
- Residual PHI detection

### Interface Layer (介面層)
User-facing interfaces.
- CLI implementation
- API endpoints (future)

## Development Status | 開發狀態

✅ **Completed | 已完成:**
- Project structure with DDD layers
- Domain models (MedicalDocument, PHIEntity, RegulationContext)
- Unit test framework and fixtures
- Poetry project configuration
- Memory Bank architecture documentation

🚧 **Next Steps | 下一步:**
- Implement Module 1: Document Loader
- Implement Module 2: RAG Regulation Engine (Innovation core)
- Implement Module 4: LLM Integration
- Setup CI/CD with GitHub Actions
- Create GitHub repository
