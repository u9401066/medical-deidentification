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
