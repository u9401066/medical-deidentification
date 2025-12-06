# System Patterns

## Development Guidelines | 開發準則

### Language Standards | 語言標準
- **繁體中文 (Traditional Chinese)**: 用於註解、文件及溝通
- **Academic English**: For technical documentation and code

### Documentation Protocol | 文件協定
- 所有文件變更必須更新 Memory Bank (MEM)
- Memory Bank serves as the single source of truth for project context

### Version Control Practice | 版本控制實踐
- **GIT + MEM 原則**: 所有程式碼變更必須同時：
  - Commit to Git repository
  - Update relevant Memory Bank files
  - 確保版本控制與知識管理同步

### Development Methodology | 開發方法論
- **MVP Principle (Minimum Viable Product)**: 
  - 優先實作核心功能
  - Iterative development with incremental delivery
  - Focus on delivering value early and often

- **DDD (Domain-Driven Design)**:
  - 以領域模型為中心的設計
  - Ubiquitous language across team
  - Bounded contexts for module separation
  - Rich domain models with encapsulated business logic

## Architectural Patterns

### 1. Modular Architecture | 模組化架構

The system is designed with **6 core modules** for clear separation of concerns:

系統設計採用 **6 個核心模組**,實現清晰的關注點分離:

#### Module 1: Document Loader | 文本載入模組
- **Pattern**: Adapter Pattern
- **Purpose**: Adapt various document formats to unified internal representation
- 適配多種文件格式到統一內部表示
- **Responsibilities**: 
  - Format parsing (TXT, JSON, CSV, FHIR)
  - Text extraction and normalization
  - Metadata extraction

#### Module 2: RAG Regulation Engine | RAG 規範引擎 ⭐ 創新核心
- **Pattern**: Strategy Pattern + Repository Pattern
- **Purpose**: Retrieve regulation rules dynamically using RAG
- 使用 RAG 動態檢索法規規則
- **Key Innovation**: RAG retrieves "what to mask" instead of "what to preserve"
- **關鍵創新**: RAG 檢索「需要遮蔽的內容」而非「需要保留的內容」
- **Responsibilities**:
  - Query vector database of regulations (HIPAA, GDPR)
  - Semantic search for applicable PHI detection rules
  - Generate context-specific masking instructions
  - Preserve non-PHI content integrity

#### Module 3: Core Processing Engine | 核心處理引擎
- **Pattern**: Facade Pattern + Chain of Responsibility
- **Purpose**: Orchestrate the complete de-identification workflow
- 協調完整的去識別化工作流程
- **Responsibilities**:
  - Coordinate between all modules
  - Manage processing pipeline
  - Handle state transitions
  - Error recovery and retry logic

#### Module 4: LLM Integration Layer | LLM 串接層
- **Pattern**: Adapter Pattern + Factory Pattern
- **Purpose**: Abstract LLM provider differences
- 抽象化不同 LLM 提供者的差異
- **Responsibilities**:
  - Provider abstraction (OpenAI, Anthropic, local models)
  - Prompt template management
  - Response parsing and validation
  - Rate limiting and retry mechanisms

#### Module 5: Output Module | 輸出模組
- **Pattern**: Builder Pattern + Template Method
- **Purpose**: Format and export processing results
- 格式化並匯出處理結果
- **Responsibilities**:
  - Multiple format support (JSON, CSV, TXT, FHIR)
  - Audit log generation
  - Report creation
  - Optional encryption for sensitive mappings

#### Module 6: Validation & Quality Assurance | 檢核模組
- **Pattern**: Observer Pattern + Specification Pattern
- **Purpose**: Ensure de-identification quality and compliance
- 確保去識別化品質與合規性
- **Responsibilities**:
  - Residual PHI detection
  - Quality metrics calculation (precision, recall, F1)
  - Compliance validation (HIPAA, GDPR)
  - Validation report generation

### 2. RAG-Enhanced De-identification Pattern | RAG 增強去識別化模式

**Problem**: Traditional de-identification may over-mask content or miss context-specific PHI.
**問題**: 傳統去識別化可能過度遮蔽或遺漏上下文特定的個資。

**Solution**: Use RAG to retrieve precise masking rules from regulation knowledge base.
**解決方案**: 使用 RAG 從法規知識庫檢索精確的遮蔽規則。

**Benefits**:
- Context-aware PHI detection based on actual regulations
- 基於實際法規的上下文感知個資檢測
- Minimize false positives (unnecessary masking)
- 最小化誤檢（不必要的遮蔽）
- Maintain document readability and utility
- 維持文件可讀性與實用性
- Easy to update regulations without code changes
- 易於更新法規而無需更改程式碼

**Implementation**:
```python
# Pseudocode
regulation_context = rag_engine.retrieve_rules(document_context)
masking_instructions = regulation_context.generate_instructions()
detected_phi = llm.detect_phi(text, masking_instructions)
deidentified = apply_strategy(detected_phi, preserve_non_phi=True)
```

### 3. Testing Strategy Pattern | 測試策略模式

**Principle**: Comprehensive testing at all levels
**原則**: 各層級的全面測試

**Test Levels**:
1. **Unit Tests**: Individual module functions
   - 單元測試: 個別模組功能
2. **Integration Tests**: Module interactions
   - 整合測試: 模組互動
3. **End-to-End Tests**: Complete workflows
   - 端到端測試: 完整工作流程
4. **Quality Tests**: PHI detection accuracy
   - 品質測試: 個資檢測準確度
5. **Compliance Tests**: Regulation adherence
   - 合規測試: 法規遵循

**Test Data**:
- Synthetic medical records (never real PHI)
- 合成醫療記錄（絕不使用真實個資）
- Known PHI entity test cases
- Edge cases and boundary conditions

## Design Patterns

- Pattern 1: Description

## Common Idioms

- Idiom 1: Description

## Structured Output from RAG/LLM

使用 LangChain structured output + Pydantic models 確保 RAG/LLM 返回類型安全的結構化資料，而非依賴 JSON string parsing。

Pattern 結構：
1. 定義 Pydantic BaseModel 作為輸出 schema (PHIIdentificationResult)
2. 使用 LangChain llm.with_structured_output(schema) 強制 LLM 遵守 schema
3. LLM 輸出自動驗證並映射到 Pydantic model instances
4. 將 Pydantic models 轉換為 domain models (PHIEntity)

優勢：
- 類型安全：編譯時檢查，運行時驗證
- 減少錯誤：無需手動 JSON parsing
- 可維護：Schema 集中定義
- 可測試：Mock Pydantic instances

適用場景：
- RAG 系統需要結構化 PHI 識別結果
- LLM 需要返回複雜的嵌套結構
- API 響應需要強類型保證

### Examples

- infrastructure/rag/regulation_chain.py: RegulationRAGChain.identify_phi() 使用 structured output
- domain/models.py: PHIEntity 作為 domain model
- application/processing/engine.py: 消費結構化 PHI 結果


## Structured Output with Enum Types

Use str-based Enum in Pydantic models for LLM structured output to combine type safety with JSON compatibility. PHIType enum demonstrates this pattern: inherits both str and Enum, provides validators for flexible input, and ensures type-safe output throughout the system.

### Examples

- medical_deidentification/domain/models.py: class PHIType(str, Enum)
- medical_deidentification/infrastructure/rag/regulation_chain.py: class PHIIdentificationResult(BaseModel) with phi_type: PHIType field
- Validator automatically converts LLM string outputs to PHIType enum values


## Dynamic PHI Type Extension Pattern

Use CustomPHIType to extend PHIType enum dynamically based on regulation discovery. When RAG retrieves regulations containing country-specific or institution-specific identifiers, create CustomPHIType instances with pattern matching, masking strategies, and risk levels. PHIEntity uses PHIType.CUSTOM + custom_type field to represent extended types while maintaining type safety.

### Examples

- Taiwan National ID (身份證字號): CustomPHIType with pattern r'[A-Z][12]\d{8}'
- Japan My Number (マイナンバー): CustomPHIType with pattern r'\d{12}'
- Hospital rare disease policy: CustomPHIType with aliases=['Gaucher', '戈謝', '高雪氏']
- PHIEntity(type=PHIType.CUSTOM, custom_type=tw_national_id, ...)


## LLM 創建和管理的統一模式

系統中所有 LLM 的創建和管理都統一通過 infrastructure/llm 模組進行：

**架構層次**：
1. **Config Layer** (config.py): 統一的 LLMConfig 配置類 + LLMPresets 預設配置
2. **Factory Layer** (factory.py): create_llm() 工廠函數，根據 config 創建對應的 LLM 實例
3. **Manager Layer** (manager.py): LLMManager 高階管理介面，提供懶載入、統計追蹤、批次處理等功能

**設計原則**：
- 單一職責：LLM 創建邏輯只存在於 llm 模組
- 依賴反轉：使用 LLMConfig 抽象，不直接依賴 ChatOpenAI/ChatAnthropic
- 開放封閉：新增 provider 只需修改 factory.py，不影響現有代碼
- DRY 原則：避免在多處重複 LLM 創建代碼

**使用模式**：
```python
# 方式 1: Factory (簡單場景)
from infrastructure.llm import create_llm, LLMConfig
config = LLMConfig(provider="openai", model_name="gpt-4")
llm = create_llm(config)

# 方式 2: Presets (常見場景)
from infrastructure.llm import create_llm, LLMPresets
config = LLMPresets.phi_identification()
llm = create_llm(config)

# 方式 3: Manager (進階場景)
from infrastructure.llm import LLMManager
manager = LLMManager(config)
response = manager.invoke("prompt")
stats = manager.get_stats()
```

**向後兼容**：
- create_regulation_rag_chain() 仍接受 llm_provider/model_name 參數
- 內部自動轉換為 LLMConfig

### Examples

- medical_deidentification/infrastructure/llm/config.py
- medical_deidentification/infrastructure/llm/factory.py
- medical_deidentification/infrastructure/llm/manager.py
- medical_deidentification/infrastructure/rag/regulation_chain.py (使用 create_llm)


## Prompt 模板的集中管理模式

系統中所有 prompt 模板都統一通過 infrastructure/prompts 模組進行管理：

**架構設計**：
1. **templates.py**: 所有 prompt 模板定義
   - 版本化的 prompt (v1, v2, ...)
   - 多語言版本 (en, zh-TW, zh-CN)
   - PROMPT_REGISTRY 統一註冊
   - 存取函數 (get_prompt, get_phi_identification_prompt, etc.)

2. **__init__.py**: 統一導出所有公開 API

**設計原則**：
- 單一真相來源：所有 prompts 定義在一處
- 版本控制：支援多版本共存
- 多語言：統一管理不同語言版本
- 易測試：可獨立驗證 prompt 格式
- 向後兼容：保留直接存取方式

**使用模式**：
```python
# 方式 1: 便捷函數（推薦）
from infrastructure.prompts import get_phi_identification_prompt
prompt = get_phi_identification_prompt(language="en", structured=True)

# 方式 2: 完全控制
from infrastructure.prompts import get_prompt
prompt = get_prompt("phi_identification", language="zh-TW", version="v1")

# 方式 3: 直接存取（向後兼容）
from infrastructure.prompts import PHI_IDENTIFICATION_PROMPT
prompt = PHI_IDENTIFICATION_PROMPT
```

**擴展方式**：
1. 新增語言：在 templates.py 中添加新的語言版本到 PROMPT_REGISTRY
2. 新增版本：創建 *_V2 常數並更新 PROMPT_REGISTRY
3. 新增 prompt 類型：添加新的 prompt 常數和對應的 get_* 函數

### Examples

- medical_deidentification/infrastructure/prompts/templates.py
- medical_deidentification/infrastructure/prompts/__init__.py
- medical_deidentification/infrastructure/rag/regulation_chain.py (使用 get_phi_identification_prompt)


## RAG Chain 的職責分離模式

RAG Chain 應該按照數據來源和用途分離：(1) RegulationRetrievalChain: 從持久化法規向量庫檢索 PHI 定義和 masking 策略，使用 RegulationRetriever；(2) PHIIdentificationChain: 從臨時醫療文本中識別具體 PHI 實體，使用 MedicalTextRetriever + 法規 context。兩者可以組合但不應混在同一個 class (當前 RegulationRAGChain 716 行過長且職責混淆)。共用部分：LLM factory, Prompts module。

### Examples

- 待重構: infrastructure/rag/regulation_chain.py (拆分為兩個 chain)
- infrastructure/rag/regulation_retriever.py (持久化法規)
- infrastructure/rag/medical_retriever.py (臨時醫療文本)


## Engine 模組化架構 (Modular Engine Architecture)

將大型單一檔案重構為模組化資料夾結構，每個模組專注於單一職責。原 engine.py (718 lines) 拆分為 6 個模組：config.py (配置)、result.py (結果)、masking.py (遮蔽邏輯)、handlers.py (Pipeline處理器)、core.py (主引擎協調)、__init__.py (統一導出)。每個模組平均 ~206 lines，易於閱讀和維護。優勢：SRP、易測試、易擴展、向後兼容。

### Examples

- medical_deidentification/application/processing/engine/ - 6 個模組檔案
- config.py - ProcessingStatus, EngineConfig
- result.py - ProcessingResult with helper methods
- masking.py - MaskingProcessor class
- handlers.py - PipelineHandlers factory
- core.py - DeidentificationEngine (主引擎)


## FIFO Streaming Pattern

Process data in chunks with immediate output and memory release. Pattern: iterate → process → output → release → next. Enables unlimited input size with constant memory usage. Checkpoint saves after each chunk for resume capability.

### Examples

- StreamingChunkProcessor.chunk_iterator() - yields one chunk at a time
- StreamingPHIChain.process_file() - FIFO PHI detection
- ProcessingCheckpoint - resume from last completed chunk



## Python Virtual Environment

Project uses pure Python 3.11 venv (not Anaconda) at `.venv/`. Always use `D:/workspace251122/.venv/Scripts/python.exe` or `py -3.11` to run Python commands. This ensures clean dependencies without Anaconda path pollution.

### Examples

- D:/workspace251122/.venv/Scripts/python.exe -m pytest tests/
- D:/workspace251122/.venv/Scripts/pip.exe install package
- py -3.11 -m venv .venv


Project uses venv at `.venv/`. Always use `D:/workspace251122/.venv/Scripts/python.exe` to run Python commands instead of system Python. This ensures correct dependencies and isolation.

### Examples

- D:/workspace251122/.venv/Scripts/python.exe -m pytest tests/
- D:/workspace251122/.venv/Scripts/python.exe script.py



## LLM Model Priority

Default LLM models: qwen2.5:1.5b or minimind first, llama3.1:8b as backup only. Smaller models are preferred for faster response and lower resource usage.

### Examples

- jingyaogong/minimind2:latest (208MB)
- qwen2.5:1.5b (986MB)
- qwen2.5:3b (1.9GB)
- llama3.1:8b (4.9GB) - backup only


Default LLM models: Primary is qwen:1.5b + minimind for speed. Backup is llama3.1:8b for quality. Always try smaller models first.

### Examples

- LLMConfig(provider='ollama', model_name='qwen:1.5b')
- LLMConfig(provider='ollama', model_name='minimind')
