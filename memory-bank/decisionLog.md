# Decision Log

## Core Principles | 核心原則

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-22 | GIT + MEM 同步原則 | 所有變更必須同時提交 Git 和更新 Memory Bank,確保版本控制與知識管理一致性 |
| 2025-11-22 | Memory Bank 作為唯一真實來源 | 所有專案知識必須透過 Memory Bank 記錄和更新 |
| 2025-11-22 | 繁體中文 + 學術英文雙語 | 技術文件用英文,註解和溝通用繁體中文,確保國際標準與本地化平衡 |
| 2025-11-22 | MVP 開發原則 | 優先實作核心功能,快速迭代交付,及早獲得回饋 |
| 2025-11-22 | DDD (Domain-Driven Design) | 四層架構: Domain (模型/配置) → Application (用例) → Infrastructure (技術實作) → Interface (CLI) |
| 2026-01-14 | Frontend DDD 架構 | 前端採用相同 DDD 分層：domain → application → infrastructure → presentation |

## Architecture Decisions | 架構決策

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-22 | 6 個核心模組設計 | (1) Document Loader (2) **RAG Regulation Engine** (3) Core Processing (4) LLM Integration (5) Output (6) Validation。模組化設計,清晰分離關注點 |
| 2025-11-22 | RAG 創新: 檢索「需要遮蔽的內容」 | 傳統方法檢索「要保留的內容」易過度遮蔽。RAG 從法規文件檢索「需遮蔽的 PHI 類型」,提高精準度和可讀性 |
| 2025-11-22 | 隱私優先: In-memory 處理 | 法規文件持久化 (FAISS),醫療文本僅在記憶體處理 (不持久化),確保個資安全 |
| 2025-11-22 | LangChain 作為 RAG/LLM 框架 | 統一管理 LLM/RAG/Agent,豐富生態系統,支援多 provider (OpenAI/Anthropic/Ollama) |
| 2025-11-22 | 結構化輸出 (Pydantic + LangChain) | 使用 Pydantic BaseModel + with_structured_output() 確保類型安全,避免 JSON parsing 錯誤 |
| 2025-11-22 | 可擴充 PHI 類型系統 | 28 標準類型 + CustomPHIType 動態擴展,支援不同國家/法規/機構需求 |
| 2025-11-22 | 多語言支援 (10+ 語言) | 支援繁中/簡中/英/日/韓/西/法/德/泰/越,使用 SupportedLanguage 枚舉確保類型安全 |
| 2026-01-14 | Frontend 日誌可讀取 | 前端日誌必須輸出到 console,並存於 window.__FRONTEND_LOGS__ 供 Agent 讀取 |
| 2026-01-14 | 前端自動測試套件 | 使用 Vitest + React Testing Library,覆蓋率要求 domain≥90%, application≥80%, presentation≥70% |

## Technical Patterns | 技術模式

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-22 | 統一 LLM 管理模組 (infrastructure/llm) | config.py (配置) + factory.py (創建) + manager.py (管理),避免重複代碼,易於擴展 |
| 2025-11-22 | 統一 Prompt 管理模組 (infrastructure/prompts) | 版本控制 (v1/v2) + 多語言 + 集中管理,單一真相來源 |
| 2025-11-22 | RAG Chain 職責分離 | RegulationRetrievalChain (法規檢索) + PHIIdentificationChain (PHI識別),符合單一職責原則 |
| 2025-11-22 | 模組化架構 (例: engine/, chains/, prompts/) | 大文件拆分為多個小模組,每個 ~200 行,易讀易維護 |
| 2025-11-22 | LangChain Runnable 模式 | 所有 chain 使用 Runnable (prompt \| llm),可組合、可測試、一致性 |
| 2025-11-22 | MapReduce 處理長文本 | Map 階段: 每個 chunk 提取 PHI (短 prompt),Reduce 階段: 合併去重 (無需 LLM) |

## Implementation Decisions | 實作決策

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-22 | Ollama 作為本地 LLM | 開源免費,支援多模型,易部署,與 LangChain 良好整合,保護醫療數據隱私 |
| 2025-11-22 | GPU 硬體加速支援 | LLMConfig 支援 use_gpu/num_gpu/gpu_layers,自動檢測 GPU,3-5x 速度提升 |
| 2025-11-22 | torch 2.2.0+cpu + numpy <2.0 | torch 2.9.1 在 Windows 有 DLL 問題,固定版本確保穩定性 |
| 2025-11-22 | langchain 1.0+ 生態系統 | 升級到最新穩定版,避免 deprecation warnings 和未來相容性問題 |
| 2025-11-22 | 清理測試文件原則 | 每功能只保留一個測試腳本,臨時診斷腳本完成後必須刪除 |
| 2025-11-22 | 測試日誌政策 | 所有測試生成時間戳日誌,執行後必須檢查,保留 10 天/10MB 輪替 |
| 2025-11-22 | Prompt 年齡規則優化 | "Ages ONLY if >90" (否定句) 避免誤判年輕人,符合 HIPAA 安全港規則 |
| 2025-11-23 | PHI 檢測評估工具 | generate_test_data_with_phi_tags.py (107 標記 PHI) + phi_evaluator.py (Precision/Recall/F1) |
| 2025-11-23 | 刪除過時文檔保持整潔 | 開發過程中的臨時記錄 (PACKAGE_VERSIONS.md 等) 完成目的後刪除,核心功能完好 |

---

**更新時間**: 2025-11-23  
**文件狀態**: ✅ 精簡整理完成
| 2025-11-22 | 文件更新必須透過 Memory Bank | Memory Bank 作為專案知識的唯一真實來源 |
| 2025-11-22 | 採用 MVP 開發原則 | 快速交付價值,透過迭代降低風險,及早獲得回饋 |
| 2025-11-22 | 採用 DDD (Domain-Driven Design) | 以業務領域為核心,建立清晰的領域邊界,提升系統可維護性 |
| 2025-11-22 | 採用 6 個核心模組架構設計 | 根據使用者需求設計：(1)文本載入模組 (2)RAG規範引擎-檢索要遮蔽的內容而非要保留的 (3)核心處理引擎 (4)LLM串接層 (5)輸出模組 (6)檢核模組。這種模組化設計符合DDD原則,清晰分離關注點,易於測試與擴展。 |
| 2025-11-22 | RAG 檢索「需要遮蔽的內容」創新設計 | 傳統方法檢索「要保留的內容」容易造成過度遮蔽。創新方法使用RAG檢索法規文件,明確指出「哪些內容需要遮蔽」,保留其他內容不受影響,提高去識別化精準度與文件可讀性。 |
| 2025-11-22 | 支援至少 10 種語言的多語言去識別化 | 醫療文本去識別化需要支援多種語言以應對國際化需求。實作 SupportedLanguage 枚舉支援：繁體中文、簡體中文、英文、日文、韓文、西班牙文、法文、德文、泰文、越南文等 10 種語言（可擴充）。使用枚舉確保類型安全，並提供語言驗證方法。 |
| 2025-11-22 | 實作可擴充的 PHI 類型系統 | PHI 識別需求因法規、機構政策和使用情境而異。實作包含：(1) 擴充標準 PHI 類型至 20+ 種，包括病房號、醫院名稱、年齡>90、罕見疾病等 (2) CustomPHIType 允許使用者定義自定義類型 (3) 支援 standard/strict 嚴格程度 (4) 高風險 PHI 標記機制 (5) 透過 RAG 從法規文件動態檢索所需的 PHI 類型。此設計平衡了標準化與靈活性。 |
| 2025-11-22 | 建立依賴管理策略：所有套件安裝必須同步更新 MEM + requirements.txt | 確保專案依賴可追溯且可重現。規範：(1) 使用 Poetry 管理依賴 (2) 每次安裝新套件後立即執行 poetry export 生成 requirements.txt (3) 在 MEM decisionLog 記錄安裝原因 (4) 更新 progress.md 記錄進度。此策略確保團隊成員和 CI/CD 環境能夠準確重現開發環境。 |
| 2025-11-22 | 安裝測試檔案生成所需套件：openpyxl 和 python-docx | 為了建立測試用的多格式病歷檔案（XLSX, DOCX, TXT），需要安裝文件處理套件。openpyxl 用於處理 Excel 檔案，python-docx 用於處理 Word 檔案。這些套件也將用於未來的 Document Loader 模組實作。 |
| 2025-11-22 | RAG架構選擇：使用 LangChain 而非 LightRAG，採用 in-memory vector store (無持久化) | 1. LangChain 優勢：統一管理 LLM/RAG/Agent，豐富的生態系統，支援多種 LLM provider (OpenAI, Anthropic, 本地模型)
2. LightRAG 劣勢：較新框架，生態系統較小，文檔較少，不確定是否支援 in-memory 模式
3. 隱私要求：不持久化 vector store 以避免儲存個資（regulations 可持久化，但病歷文本僅在記憶體處理）
4. 實作策略：LangChain + FAISS (in-memory) / Chroma (ephemeral mode) 作為 vector store
5. RAG 目標：從 regulation documents 檢索「需要遮罩的個資類型」，而非傳統「保留資訊」的 RAG 模式 |
| 2025-11-22 | RAG 基礎設施實作完成：實作 regulation_store.py (RegulationVectorStore + InMemoryDocumentProcessor), retriever.py (RegulationRetriever with MMR), regulation_chain.py (RegulationRAGChain with LLM integration) | 完成 RAG 基礎設施核心模組，提供：1) 持久化法規向量庫（FAISS）+ 臨時病歷處理（in-memory），確保隱私設計；2) MMR 檢索器，平衡相關性與多樣性；3) LangChain RetrievalQA 鏈，整合 OpenAI/Anthropic LLM 進行 PHI 識別；4) 完整使用範例（8個場景）和詳細文檔（RAG_USAGE_GUIDE.md），提供雙語說明和最佳實踐。系統已具備完整 RAG 功能框架，待安裝依賴後可測試。 |
| 2025-11-22 | Document Loader 模組實作完成：支援 10 種文件格式（TXT, CSV, XLSX, XLS, DOCX, JSON, PDF, HTML, XML, FHIR），使用工廠模式和策略模式設計，提供統一載入介面 | 實作完整的文件載入模組，解決醫療文件多格式問題：1) 抽象基類（DocumentLoader）定義統一介面；2) 格式特定載入器（TextLoader, ExcelLoader等）處理各格式細節；3) 工廠類（DocumentLoaderFactory）自動選擇載入器；4) 配置類（LoaderConfig）提供靈活設定（編碼、分頁、工作表選擇等）；5) LoadedDocument 統一返回格式（含元數據、內容、結構化資料）；6) 完整錯誤處理和日誌記錄。新增依賴：xlrd（XLS支援）、PyPDF2/pdfplumber（PDF）、beautifulsoup4（HTML）。提供 18 個使用範例涵蓋所有場景。 |
| 2025-11-22 | RAG 系統應返回結構化的 PHI 識別結果，而非純文字 | 當前 RegulationRAGChain.identify_phi() 依賴 LLM 返回 JSON 格式字串，但缺乏：
1. 強制結構化輸出 - 需使用 Pydantic models + LangChain structured output
2. Domain models 對齊 - PHIEntity 已定義完整結構但未與 RAG 整合
3. 類型安全 - LLM 輸出需驗證並映射到 domain.models.PHIEntity
4. 錯誤處理 - JSON parsing 失敗時無降級策略

解決方案：
- 定義 PHIIdentificationResult(BaseModel) 作為 LLM structured output schema
- 使用 LangChain with_structured_output() 強制 LLM 返回符合 schema 的結果
- 映射 LLM 輸出到 PHIEntity domain model
- 添加 validation + fallback 機制

優勢：
- 類型安全：編譯時檢查 PHI 結構
- 可測試：Mock structured responses
- 可維護：Schema 集中管理
- 可靠：LLM 輸出必須符合 domain model 定義 |
| 2025-11-22 | PHIType is the Structured Output Model for RAG system | PHIType enum serves as the core type system for RAG's structured output:

1. Type Safety: PHIType (Enum) ensures type-safe PHI classification instead of error-prone strings
2. Pydantic Integration: Works seamlessly with Pydantic BaseModel for LLM structured output validation
3. JSON Serialization: str-based Enum allows direct JSON serialization/deserialization
4. LLM Output Parsing: Validator converts LLM text output ("name", "姓名") to PHIType.NAME automatically
5. Extensibility: Supports 28 PHI types (7 standard HIPAA + 21 extended) with helper methods

Updated PHIIdentificationResult model to use PHIType instead of str for phi_type field, providing compile-time type checking and runtime validation. |
| 2025-11-22 | Enable dynamic PHI type extension through CustomPHIType for regulation-discovered types | PHI types vary significantly across countries, regulations, and institutions. CustomPHIType enables:

1. Regulation Discovery: RAG can discover country-specific identifiers from regulation documents (e.g., Taiwan National ID, Japan My Number)
2. Pattern Matching: Supports regex patterns, examples, and aliases for flexible detection
3. Risk Classification: Each custom type can be marked as high-risk
4. Masking Strategy: Includes recommended masking approach per regulation
5. Seamless Integration: Works with PHIEntity (type=PHIType.CUSTOM + custom_type)
6. Context Awareness: RegulationContext manages discovered custom types

Real-world examples:
- Taiwan: 身份證字號 (National ID), 健保卡號 (Health Insurance Card)
- Japan: マイナンバー (My Number), 保険証番号 (Insurance Number)  
- EU: National health service numbers per country
- Disease-specific: Hospital policies for rare diseases

This design allows the system to adapt to any regulation without code changes. |
| 2025-11-22 | Refactor domain models using DDD pattern - split models.py into separate files | Original models.py was 468 lines with 8 classes, violating Single Responsibility Principle. Refactored into DDD-aligned structure:

1. phi_types.py (205 lines): PHIType enum + CustomPHIType - Core type system for RAG
2. entities.py (91 lines): PHIEntity - Domain entity representing detected PHI
3. value_objects.py (105 lines): SupportedLanguage, RegulationContext, DocumentMetadata, ValidationResult - Immutable value objects
4. aggregates.py (91 lines): MedicalDocument - Aggregate root managing the de-identification lifecycle
5. models.py (70 lines): Unified export interface for backward compatibility

Benefits:
- Separation of Concerns: Each file has single responsibility
- DDD Alignment: Clear distinction between entities, value objects, aggregates
- Maintainability: Easier to locate and modify specific concepts
- Testability: Can test each component independently (proven by 21/21 tests passing)
- Backward Compatibility: All existing imports still work via re-export

All 21 unit tests passed, confirming zero breaking changes. |
| 2025-11-22 | 統一 LLM 創建和管理到 infrastructure/llm 模組 | 重構理由：
1. **單一職責原則**：所有 LLM 初始化邏輯從 regulation_chain.py 移到專屬的 llm 模組
2. **可維護性**：集中管理 LLM 配置和創建，避免在多個文件中重複 ChatOpenAI/ChatAnthropic 創建邏輯
3. **擴展性**：未來新增其他 LLM provider（如 Google PaLM, Cohere）只需修改 llm 模組
4. **測試性**：LLM 創建邏輯可獨立測試，不依賴 RAG chain

架構設計：
- **config.py**: LLMConfig (統一配置) + LLMPresets (預設配置)
- **factory.py**: create_llm() (工廠函數) + provider-specific 創建
- **manager.py**: LLMManager (高階介面) + 懶載入 + 統計追蹤
- **__init__.py**: 統一導出所有公開 API

使用範例：
```python
# 在 regulation_chain.py 中
from ..llm.config import LLMConfig
from ..llm.factory import create_llm

config = LLMConfig(provider="openai", model_name="gpt-4")
self.llm = create_llm(config)
```

好處：
- regulation_chain.py 減少 16 行代碼（移除 _create_llm 方法）
- 不再直接 import ChatOpenAI/ChatAnthropic
- 配置更清晰（LLMConfig 替代 llm_provider/model_name/temperature 等散亂參數）
- 支援 LLMPresets.phi_identification() 等預設配置 |
| 2025-11-22 | 統一 Prompt 管理到 infrastructure/prompts 模組 | 重構理由：
1. **單一真相來源**：所有 prompt 模板從 regulation_chain.py 和測試文件移到專屬的 prompts 模組
2. **版本控制**：支援多版本 prompts (v1, v2, ...)，方便 A/B 測試和逐步升級
3. **多語言支援**：統一管理不同語言版本（English, 繁體中文, 簡體中文）
4. **可維護性**：修改 prompt 只需更新一處，不需要在多個文件中搜尋替換
5. **可測試性**：Prompt 可獨立測試格式正確性和變數完整性

架構設計：
- **templates.py** (450 lines): 所有 prompt 模板定義
  * PHI_IDENTIFICATION_PROMPT_V1: PHI 識別主 prompt
  * PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1: 結構化輸出版本
  * PHI_VALIDATION_PROMPT_V1: PHI 驗證 prompt
  * PHI_IDENTIFICATION_PROMPT_ZH_TW: 繁體中文版本
  * SYSTEM_MESSAGE_*: 系統訊息
  * PROMPT_REGISTRY: 統一註冊表
  * get_prompt(), get_phi_identification_prompt() 等存取函數

- **__init__.py** (110 lines): 統一導出所有公開 API

使用範例：
```python
# 在 regulation_chain.py 中
from ..prompts import get_phi_identification_prompt

# 動態取得 prompt
prompt = get_phi_identification_prompt(language="en", structured=True)
formatted = prompt.format(context=context, text=text)

# 或直接存取（向後兼容）
from ..prompts import PHI_IDENTIFICATION_PROMPT
```

好處：
- regulation_chain.py 減少 65+ 行（移除內嵌 prompt 定義）
- 支援版本控制：可同時維護 v1, v2 等多版本
- 支援多語言：English, 繁體中文（可輕易擴展）
- 統一管理：新增 prompt 只需在 templates.py 中定義
- 便捷函數：get_phi_identification_prompt() 等簡化使用
- 向後兼容：PHI_IDENTIFICATION_PROMPT 仍可直接存取

測試結果：8/9 測試通過 ✅ |
| 2025-11-22 | 重構 RAG Chain：分離法規檢索與醫療文本 PHI 識別 | 當前 regulation_chain.py 混淆了兩個不同職責：(1) 從法規向量庫檢索 PHI 定義 (應用 RegulationRetriever)，(2) 從醫療文本中識別具體 PHI 實體 (應用 MedicalTextRetriever)。應該拆分為：RegulationRetrievalChain (查詢法規) 和 PHIIdentificationChain (識別醫療文本中的 PHI，內部使用法規 context)。兩者可以組合使用，但職責應分離。這樣可以減少代碼長度 (716 lines 太長)，提高可維護性，符合單一職責原則。 |
| 2025-11-22 | 創建 .env 文件儲存 OpenAI API Key | 為了安全管理 API keys，創建 .env 文件儲存敏感資訊。.env 文件已在 .gitignore 中，不會被提交到 Git。專案使用 python-dotenv 讀取環境變數，支援本地開發和 CI/CD。API key 儲存後可以運行完整的 PHI identification 測試。 |
| 2025-11-22 | 更改預設 LLM 模型為 gpt-4o-mini（支持結構化輸出） | 原預設模型 gpt-4 不支持 OpenAI 的 Structured Output API。gpt-4o-mini 支持結構化輸出（with_structured_output），比 gpt-4 便宜 ~60%，速度更快，且質量接近。已驗證 OpenAI API 通過 LangChain 正確初始化，結構化輸出測試成功返回 Pydantic 模型。支持結構化輸出的模型：gpt-4o, gpt-4o-mini, gpt-4-turbo。 |
| 2025-11-22 | 清理專案中的舊測試文件和臨時文檔 | 完成多次重構後（LLM、Prompts、Retriever、RAG Chain），累積了大量臨時測試文件和重構摘要文檔。這些文件已完成其目的（驗證重構），現在清理以保持專案整潔。保留的測試文件：tests/unit/（單元測試）、tests/integration/（整合測試）、tests/e2e/（端到端測試）、examples/（示例代碼）。刪除的文件類型：1) 根目錄 test_*.py（臨時測試）；2) *_SUMMARY.md（重構摘要）；3) *_COMMIT.md（臨時 commit 訊息）；4) tests/ 中的舊測試（test_step*.py, test_rag*.py）。所有重構決策和進度已記錄在 Memory Bank 中。 |
| 2025-11-22 | 移除舊的 RAG chain 檔案（regulation_chain.py, retriever.py）和依賴舊 API 的 examples | 完成 RAG Chain 職責分離後，舊的 RegulationRAGChain (716 lines) 和 retriever.py (230 lines) 已被新的模組化 chains 取代。刪除 5 個檔案（2 個核心檔案 + 3 個 examples），更新 engine.py 使用新 API。新架構更清晰：RegulationRetrievalChain（法規檢索）+ PHIIdentificationChain（PHI識別）。 |
| 2025-11-22 | 將 engine.py (718 lines) 重構為模組化的 engine/ 資料夾結構 | 原 engine.py 過於龐大（718 行），混合了配置、結果、遮蔽邏輯、handlers 等多種職責，不符合單一職責原則。重構為 6 個模組：config.py（配置）、result.py（結果）、masking.py（遮蔽邏輯）、handlers.py（Pipeline處理器）、core.py（主引擎）、__init__.py（導出）。優勢：易讀性（每個模組~206行）、可維護性（修改局部化）、可測試性（獨立測試）、可擴展性（新增功能不影響其他）、向後兼容（import路徑不變）。 |
| 2025-11-22 | 選擇 Ollama 作為本地 LLM 解決方案 | OpenAI API 回應極慢（>5分鐘/請求），需要本地 LLM 提升測試效率。Ollama 優勢：1) 開源免費，2) 支援多種模型（Qwen, Llama, Mistral），3) 易於安裝和部署，4) 與 LangChain 整合良好，5) 保護敏感醫療數據隱私 |
| 2025-11-22 | 使用 invoke() 替代 predict() 以支援所有 LangChain chat models | ChatOllama 不支援舊版的 predict() 方法，只支援新版的 invoke() API。為了確保與 OpenAI、Anthropic、Ollama 三種 provider 的相容性，統一使用 invoke() 方法並處理回應格式差異（response.content vs str(response)）。這使得代碼更加健壯，可以無縫切換不同的 LLM provider。 |
| 2025-11-22 | Test Script Management: Only ONE test script per feature | To maintain codebase clarity and avoid confusion:
1. Each feature should have only ONE active test script
2. When updating test functionality, modify existing script OR create new one and delete old
3. Always use version control (Git) to preserve history
4. Commit changes with clear messages: "refactor: replace old_test.py with new_test.py"
5. Temporary diagnostic scripts must be deleted after debugging

Current active test: test_batch_processor.py (uses BatchPHIProcessor module)
Deleted: test_phi_batch_ollama.py, test_ollama_simple.py (replaced by integrated module) |
| 2025-11-22 | Test Logging Policy: Always check log files after test execution | To ensure proper debugging and tracking:
1. All test scripts must generate timestamped log files
2. Log filename format: test_[feature]_YYYYMMDD_HHMMSS.log
3. After each test run, ALWAYS check the log file for errors/warnings
4. Keep logs for 10 days with 10MB rotation
5. Log level: DEBUG for comprehensive troubleshooting

Current implementation:
- test_batch_processor.py generates: test_batch_YYYYMMDD_HHMMSS.log
- Captures all DEBUG/INFO/WARNING/ERROR messages
- Helps diagnose PHI identification issues (like CUSTOM type errors) |
| 2025-11-22 | PHI Type Mappings Architecture: Domain-Driven Design with Extensibility | Refactored PHI type mappings from infrastructure layer to domain layer following DDD principles:

**Before**: Hardcoded dictionary in phi_identification_chain.py (infrastructure layer)
**After**: PHITypeMapper class in domain/phi_type_mapper.py

**Key Improvements**:
1. Separation of Concerns: Business logic (type mappings) in domain layer
2. Extensibility: Easy to add custom mappings via API
3. Testability: PHITypeMapper independently testable
4. Maintainability: Single source of truth
5. Flexibility: Support per-language/regulation mappings

**API for Extension**:
```python
from core.domain import get_default_mapper

mapper = get_default_mapper()
mapper.register_custom_mapping('職業', PHIType.CUSTOM)
mapper.register_custom_type_definition('身份證', custom_type_def)
```

**Benefits for Regulations**:
- Can load mappings from regulation documents
- Support multiple language/region specific types
- CustomPHIType with pattern matching, examples, aliases
- Future: Load from config files or database |
| 2025-11-22 | Prompt Management Principle: All text content in prompts module | All prompt-related text, including default contexts and regulation rules, must be centralized in the prompts module:

**Rule**: No hardcoded prompt strings in business logic layers

**Before**: Default HIPAA rules hardcoded in phi_identification_chain.py
**After**: DEFAULT_HIPAA_SAFE_HARBOR_RULES in prompts/templates.py

**Benefits**:
1. Single source of truth for all prompts
2. Easy to update/version prompt content
3. Consistent with existing prompt architecture
4. Better testability (test prompts independently)
5. Clear separation: prompts module = content, other modules = logic

**What belongs in prompts module**:
- All LLM prompt templates
- System messages
- Default regulation contexts
- Example outputs
- Instruction text
- Few-shot examples

**What does NOT belong**:
- Business logic
- Data processing code
- Configuration (use config module instead)
- Domain models |
| 2025-11-22 | PHI Identification Models in Domain Layer (DTOs) | Moved PHIIdentificationResult, PHIDetectionResponse, and PHIIdentificationConfig from infrastructure/rag/phi_identification_chain.py to domain/phi_identification_models.py (270 lines). 

Architectural Principles:
1. DDD Alignment: DTOs representing business concepts belong in domain layer
2. Single Source of Truth: One definition for all infrastructure consumers
3. Reusability: Can be imported by any infrastructure component
4. Testability: Domain models can be tested independently

Implementation Details:
- Used Any type for llm_config field to avoid circular imports (domain shouldn't depend on infrastructure)
- Integrated PHITypeMapper into PHIIdentificationResult validators for automatic type normalization
- Added to_phi_entity() conversion method bridging DTO → domain entity
- Reduced phi_identification_chain.py from 681 lines to ~520 lines

This completes the third phase of DDD refactoring:
Phase 1: PHI type mappings → domain/phi_type_mapper.py
Phase 2: HIPAA rules → infrastructure/prompts/templates.py
Phase 3: Pydantic DTOs → domain/phi_identification_models.py

Result: Clean separation of concerns with no business logic in infrastructure layer. |
| 2025-11-22 | Domain Layer Export Structure Simplification | Removed redundant domain/models.py export layer and consolidated all exports directly in domain/__init__.py.

Problems Identified:
1. Duplicate exports: domain/__init__.py imported from domain/models.py, which re-exported the same content (80+ lines of redundancy)
2. Circular dependencies: value_objects.py imported PHIType, CustomPHIType, PHIEntity only for type hints, causing import cycles
3. Inconsistent import paths: Some code used domain.models, some used direct submodules

Refactoring Actions:
1. Deleted domain/models.py completely
2. Modified domain/__init__.py to import directly from submodules (phi_types, entities, value_objects, aggregates, phi_type_mapper, phi_identification_models)
3. Fixed circular dependencies in value_objects.py:
   - Used TYPE_CHECKING for type-only imports
   - Moved runtime PHIType import to method scope
   - Changed List[PHIType] to List["PHIType"] in type hints
4. Updated 14 files across infrastructure and application layers:
   - domain.models -> domain (simplified import path)
   - Fixed enum references (ZH_TW -> TRADITIONAL_CHINESE, EN -> ENGLISH)

Architectural Benefits:
- Single Source of Truth: Only one export point (domain/__init__.py)
- Cleaner Imports: from ...domain import X instead of from ...domain.models import X
- No Circular Dependencies: TYPE_CHECKING pattern for type hints
- Reduced Maintenance: 80+ lines of duplicate code eliminated
- Better DDD Structure: Clear file organization without intermediate layers

Verification:
- All domain imports work correctly
- All infrastructure layer imports work
- All application layer imports work
- Zero compile errors in domain layer
- BatchPHIProcessor loads successfully

This follows the principle: "Each module should export once, at the highest appropriate level." |
| 2025-11-22 | 使用 Ollama native structured output 而非 LangChain wrapper | 用戶提供的 Ollama native API 範例顯示直接使用 ollama.chat() 配合 model_json_schema() 可以更好地控制超時和錯誤處理。相比 LangChain 的 with_structured_output，native API 提供：
1. 明確的 timeout 控制（Client(timeout=120)）
2. 更直接的錯誤處理
3. 可能的性能改進（減少 LangChain 抽象層開銷）
4. 更符合 Ollama 官方推薦用法

實現時保留 LangChain fallback 確保相容性。 |
| 2025-11-22 | Prompt 年齡規則從 "especially >89" 改為 "ONLY if >90" | 原始 Prompt 中 "Ages (especially >89 years)" 語意不明確，LLM 會理解為「所有年齡都要識別，但特別注意 >89」，導致 28歲、55歲等年輕人被誤判。

改為 "Ages ONLY if >90 years (ages 90 and below should NOT be identified)" 後：
1. 明確指出只有超過 90 歲才需要去識別化
2. 加上否定句強調 90 歲以下不識別
3. 符合 HIPAA 安全港規則對高齡的定義
4. 減少 false positives

測試結果：92 歲正確識別為 AGE_OVER_90，28 歲不再被誤判。 |
| 2025-11-22 | 實現 GPU 硬體加速支援（方案 D） | 用戶要求「方案 D: Hardware Acceleration有GPU應該要去支援使用」。

實現方式：
1. 在 LLMConfig 添加 GPU 參數：
   - use_gpu: bool (預設 True) - 啟用/停用 GPU
   - num_gpu: Optional[int] - 指定 GPU 數量（None=自動檢測所有，0=CPU only）
   - gpu_layers: Optional[int] - 控制層數卸載（None=全部，0=CPU only）

2. 在 factory.py 通過環境變數控制 Ollama：
   - 設定 OLLAMA_NUM_GPU 環境變數
   - 自動檢測並使用所有可用 GPU（預設行為）
   - 支援強制 CPU-only 模式（測試用）

3. 驗證 GPU 正在使用：
   - `ollama ps` 顯示 "100% GPU"
   - 日誌顯示 "processor=GPU (auto)"

預期性能提升：
- CPU-only: 30-50 秒/行
- GPU (auto): 5-15 秒/行
- 加速比: 3-5x

這是最直接且有效的速度優化方案，無需犧牲準確度，也不需要修改 Prompt 或更換模型。用戶的 GPU 已經在使用中，現在程式碼層面也正式支援配置。 |
| 2025-11-22 | 遷移到新的 LangChain 套件結構並清理依賴 | 用戶要求「一個一個file去檢查import有無正確」並「整理完也要更新requirement.txt」。

**問題診斷**：
- LangChainDeprecationWarning: ChatOllama 在 LangChain 0.3.1 已棄用
- 舊導入：from langchain_community.chat_models import ChatOllama
- 舊導入：from langchain_community.embeddings import HuggingFaceEmbeddings

**解決方案**：
1. 遷移到新套件：
   - langchain-ollama==1.0.0 (ChatOllama)
   - langchain-huggingface==1.0.1 (HuggingFaceEmbeddings)
   - ollama==0.6.1 (native structured output support)

2. 保持正確的導入：
   - langchain_community.vectorstores.FAISS (仍然正確)
   - langchain_community.document_loaders (仍然正確)

3. 清理 requirements.txt：
   - 移除未使用的套件：python-dotenv, typer, rich, tqdm, pyyaml, pandas
   - 只包含代碼中實際導入的 26 個套件
   - 所有版本號與安裝版本匹配

**驗證結果**：
- ✅ 無 LangChain deprecation warnings
- ✅ 所有導入成功
- ✅ check_dependencies.py 通過 (26/26 packages)

**遷移好處**：
- 符合 LangChain 1.0+ 結構
- 更快的導入速度（更小的套件）
- 未來兼容性（deprecated 套件將在未來版本移除）
- 更清晰的套件組織

這確保了系統使用最新、穩定的 LangChain 生態系統，避免未來的兼容性問題。 |
| 2025-11-22 | 升級 langchain 生態系統到新版本 (1.0+) | 舊版 langchain 0.1.x 與新安裝的套件版本衝突，導致 ImportError。升級到 langchain 1.0+, langchain-core 1.1+, anthropic 0.40+ 以解決依賴衝突。同時新增 langchain-huggingface 支援 embeddings。 |
| 2025-11-22 | 修正 llm_config 類型處理：factory.py 和 phi_identification_chain.py 現在可以處理 dict 或 LLMConfig 對象 | PHIIdentificationConfig 的 llm_config 被設計為 Any 類型（可接受 dict 或對象）以避免循環依賴，但下游代碼期望 LLMConfig 對象。修改了 factory.py 在創建 LLM 時自動轉換 dict 為 LLMConfig，並修改 phi_identification_chain.py 在日誌記錄時處理兩種類型 |
| 2025-11-22 | 固定 torch 版本為 2.2.0+cpu 並限制 numpy < 2.0 | torch 2.9.1 在 Windows 上有 c10.dll 載入失敗問題，降級到 2.2.0+cpu 可正常運作。torch 2.2.0 需要 numpy 1.x，因此將 numpy 限制在 <2.0。這些版本約束已記錄在 pyproject.toml 和 PACKAGE_VERSIONS.md 中 |
| 2025-11-22 | 升級整個 langchain 生態系統到 1.0.x 並新增專用提供商套件 | langchain 0.1.0 與 langchain-core 1.1.0 有嚴重的 API 不相容問題。升級到 langchain 1.0+ 並新增 langchain-anthropic, langchain-openai, langchain-ollama, langchain-huggingface 等專用套件，解決了 ImportError 並提供更好的模組化架構 |
| 2025-11-22 | 移除 60+ 個未使用的套件以精簡依賴 | 分析代碼後發現多個套件類別完全未被使用：ChromaDB（我們用 FAISS）、Kubernetes、LangGraph（不用 agent）、FastAPI/Web（命令列工具）、PDF/文件處理、spaCy/NLP。移除這些套件後從 260+ 減少到 200 個套件，大幅降低依賴複雜度，且所有 import 仍正常運作 |
| 2025-11-23 | Implement MapReduce pattern for PHI identification to fix Ollama timeout | Root cause analysis revealed the problem is NOT Ollama (works in 3-7 seconds for short prompts) but prompt length (1579 chars with 800-char context causes >150 second timeout). Current chain doesn't use LangChain mechanisms properly (no PromptTemplate, no token management, direct string concatenation). MapReduce solution: Map stage extracts PHI only from each chunk (~300-500 char prompts), Reduce stage merges results without LLM. This keeps individual requests short while processing long documents. |
| 2025-11-23 | Fix CUSTOM PHI type validation to prevent "custom_type must be provided" errors | When LLM returns unknown PHI types (e.g., "身份證字號"), PHITypeMapper converts them to PHIType.CUSTOM but custom_type_name was not always set. Added fallback in normalize_phi_type validator to always ensure custom_type_name is populated (either from mapper or using original string). This prevents validation errors during PHI entity creation. |
| 2025-11-23 | Modularize PHIIdentificationChain from 935 lines to 236 lines by extracting into chains/ submodule | Original phi_identification_chain.py violated Single Responsibility Principle with 16 methods (935 lines). Split into 4 specialized modules:
1. chains/utils.py - Utility functions (context retrieval, entity deduplication, validation)
2. chains/map_reduce.py - MapReduce pattern for long texts (3 functions: build_map_chain, merge_phi_results, identify_phi_with_map_reduce)
3. chains/processors.py - Core processing logic (3 functions: identify_phi_structured, identify_phi_json_fallback, identify_phi_direct)
4. chains/__init__.py - Unified exports

Main class now only contains:
- Public API (identify_phi)
- Thin wrapper methods delegating to imported functions
- Configuration and initialization

Benefits:
- 75% code reduction in main file (935 → 236 lines)
- Single Responsibility Principle compliance
- Improved testability (isolated functions)
- Easier maintenance and extension
- Better code organization

Deleted obsolete code:
- _old_identify_phi_chunked (replaced by MapReduce)
- batch_identify (redundant with BatchPHIProcessor) |
| 2025-11-23 | Enforce LangChain Runnable pattern across all RAG chains | Original RAG implementation had inconsistent chain patterns - some components directly called LLM, others mixed direct calls with chain patterns. Refactored to enforce LangChain Runnable pattern throughout:

1. **Prompt Centralization**:
   - Added PHI_MAP_REDUCE_PROMPT_V1 to prompts/templates.py
   - Added get_phi_map_reduce_prompt() accessor
   - All chains now use centralized prompts module

2. **Chain Pattern Enforcement**:
   - map_reduce.py: build_map_chain() returns Runnable (prompt | llm.with_structured_output)
   - processors.py: build_phi_identification_chain() returns Runnable
   - utils.py: validate_entity() uses chain (prompt | llm | JsonOutputParser)

3. **Benefits**:
   - **Composability**: Chains can be easily composed and tested
   - **Consistency**: All components follow same pattern
   - **Testability**: Runnables are unit-testable without LLM calls
   - **Maintainability**: Centralized prompts, single source of truth
   - **Error Handling**: Consistent error propagation through chains
   - **Type Safety**: LangChain Runnable provides better type hints

4. **Factory Pattern**:
   - All LLM creation uses create_llm() factory
   - No direct imports of ChatOllama, ChatOpenAI, etc.

This aligns with LangChain best practices (LCEL - LangChain Expression Language) and makes the codebase more maintainable and testable. |
| 2025-11-23 | Modularize prompts module from monolithic 429-line file into 5 specialized files | Original templates.py was 429 lines containing all prompts, system messages, registry, and accessor functions in one file - violating Single Responsibility Principle and making it hard to navigate.

**New Modular Structure**:

1. **phi_prompts.py (160 lines)**:
   - All PHI identification prompts (v1, structured, multilingual)
   - Validation prompts
   - Masking strategy prompts
   - MapReduce prompts
   - Backward compatibility aliases

2. **system_messages.py (41 lines)**:
   - System messages for different agent roles (PHI expert, regulation analyst)
   - Multilingual system messages (en, zh-TW)
   - DEFAULT_HIPAA_SAFE_HARBOR_RULES context

3. **registry.py (74 lines)**:
   - PromptType and PromptLanguage enums
   - PROMPT_REGISTRY central dictionary
   - Imports from phi_prompts and system_messages

4. **accessors.py (193 lines)**:
   - get_prompt() - Generic accessor with version support
   - get_phi_identification_prompt()
   - get_phi_validation_prompt()
   - get_masking_strategy_prompt()
   - get_phi_map_reduce_prompt()
   - get_system_message()
   - list_available_prompts()
   - validate_prompt_format()

5. **templates.py (112 lines)** - Main entry point:
   - Re-exports all components from submodules
   - Maintains backward compatibility
   - Clean __all__ declaration
   - Reduced from 429 → 112 lines (74% reduction)

**Benefits**:
- **Single Responsibility**: Each file has one clear purpose
- **Navigability**: Easy to find specific prompts by category
- **Maintainability**: Changes isolated to specific files
- **Testability**: Can test each module independently
- **Backward Compatible**: All imports remain unchanged
- **Scalability**: Easy to add new prompt categories

**Files organized by concern**:
- Prompts → phi_prompts.py
- Context → system_messages.py
- Registry → registry.py
- Accessors → accessors.py
- API → templates.py (main entry)

This follows the same modular pattern as chains/ submodule. |
| 2025-11-23 | Apply strict DDD architecture by migrating all config and domain models to domain layer | **Problem**: Infrastructure layer had scattered BaseModel classes violating DDD principles:
- 5 RAG config classes in infrastructure/rag/*.py
- 4 loader domain models in infrastructure/loader/base.py (DocumentFormat, DocumentMetadata, LoadedDocument, LoaderConfig)
- 2 empty placeholder modules (validation/, output/)

**Solution - DDD Refactoring Phase 3**:

1. **Created domain/configs.py** (112 lines)
   - Centralized 5 RAG configuration models
   - EmbeddingsConfig, RegulationStoreConfig, RegulationRetrieverConfig, RegulationRetrievalConfig, MedicalRetrieverConfig
   - All models follow consistent Field(description=...) pattern

2. **Created domain/loader_models.py** (189 lines)
   - Extracted 4 loader domain models from infrastructure/loader/base.py
   - DocumentFormat (enum with from_extension() classmethod)
   - DocumentMetadata (file info, temporal info, content info, custom metadata)
   - LoadedDocument (content, metadata, structured_data, records, __str__, __repr__)
   - LoaderConfig (encoding, content extraction, format-specific options)
   - These are business domain concepts, not infrastructure implementations

3. **Updated Infrastructure Layer** (~287 lines removed):
   - 5 RAG files: Removed config class definitions, imported from domain
   - infrastructure/loader/base.py: Removed all domain models, only kept DocumentLoader abstract class
   - Deleted empty validation/ and output/ modules

4. **Key Fixes During Migration**:
   - Added score_threshold: Optional[float] to RegulationRetrieverConfig (was used in code but missing in config)
   - Fixed MedicalRetrieverConfig field order to match actual usage (search_type first, k=3 not 5)
   - Renamed exported DocumentMetadata → LoaderDocumentMetadata (avoid conflict with value_objects.DocumentMetadata)

**DDD Principles Applied**:
✅ Domain Layer: Contains ALL business models, entities, value objects, configs
✅ Infrastructure Layer: ONLY contains technical implementations (no domain definitions)
✅ Application Layer: Orchestrates use cases, imports from domain
✅ Clear Dependencies: Infrastructure → Domain (correct), never Domain → Infrastructure

**Benefits**:
- Single Source of Truth: All configs in domain/ (no duplication)
- Better Testability: Domain models testable without infrastructure dependencies
- Clear Boundaries: Easy to understand what is "business concept" vs "technical implementation"
- Maintainability: Config changes only happen in domain layer

**This completes the 3-phase DDD migration**:
- Phase 1: PHI types → domain/phi_types.py (commit aff6cbd)
- Phase 2: PHI DTOs → domain/phi_identification_models.py (commit 4411e45)
- Phase 3: Config/loader models → domain/configs.py + domain/loader_models.py (commit 146fc3b) |
| 2025-11-23 | 刪除過時文檔文件,保持專案整潔 | 刪除 PACKAGE_VERSIONS.md, PROJECT_STATUS.md, TEST_ENGINE_QUICK.md, VERIFICATION_REPORT.md 等過時文檔和測試腳本。這些是開發過程中的臨時記錄,已不再需要。核心功能完好 (log 顯示 157 PHI 成功識別)。 |
| 2025-11-23 | Centralized Output Management: OutputManager and ReportGenerator modules | Created dedicated modules for output path management and report generation to enforce separation of concerns. Output configuration (folders, naming, timestamps) is now managed by OutputManager, and comprehensive reports are generated by ReportGenerator. This removes output logic from example files and makes the engine/processor responsible for all output operations, aligning with DDD principles where infrastructure concerns are separated from application logic. |
| 2025-12-05 | 將 output_manager 和 report_generator 從 application 層移至 infrastructure 層 | 遵循 DDD 原則：檔案 I/O 和報告生成屬於基礎設施關注點，不應放在應用層。應用層保持向後相容性的 re-export。 |
| 2025-12-05 | 整合 MiniMind 作為預設本地小型 LLM，透過 Ollama 統一介面 | 1. MiniMind 已有官方 Ollama 支援 (jingyaogong/minimind2)，無需額外整合 vLLM；2. 透過現有 Ollama provider 即可使用，保持架構一致性；3. MiniMind2 (104M) 是效能最佳版本，比 GPT-3 小約 17000 倍但仍具對話能力；4. 結構化輸出透過 LangChain + Ollama JSON mode 支援 |
| 2025-12-05 | 放棄 Python 多線程並行優化方案，改用混合 PHI 識別策略 (SpaCy + Regex + 小型 LLM) | Python 3.10 的 GIL (Global Interpreter Lock) 限制導致多線程在 CPU 密集型任務上無法真正並行執行。替代方案：1) 使用 SpaCy + Regex 快速預處理覆蓋 70-80% 標準 PHI；2) 僅對不確定區域使用小型 LLM (Qwen2.5-0.5B/1.5B)；3) 預期可達 0.1-0.5s/行的處理速度，比純 LLM 方案快 30-100 倍 |
| 2025-12-05 | 採用 Multi-Agent 架構：Router Agent 分類 + Fast/Precise Agent 處理 + 共享工具層 | 1) Router Agent (Qwen-0.5B) 快速分類每個 chunk 交給誰處理；2) SpaCy 和 Regex 作為共享工具，所有 Agent 都可調用；3) Fast Agent (MiniMind) 處理 70% 標準文本；4) Precise Agent (Qwen-1.5B) 處理 20% 複雜文本；5) 10% 純結構化 PHI 只用工具處理。這比固定管道更靈活，Agent 可根據需要自主決定是否調用工具。 |
| 2025-12-05 | 採用分階段可發布架構 (Phased Releasable Architecture) | 每個 Phase 都能獨立發布運作：Phase 1 純工具、Phase 2 單 Agent + 工具、Phase 3 多 Agent + Router、Phase 4 DSPy 優化。這樣可以逐步交付價值，不需等待全部完成。 |
| 2025-12-05 | 使用 multiprocessing Worker Pool 處理工具並發 | Python 3.10 GIL 限制多線程無法真正並行 CPU-bound 任務。使用 multiprocessing 創建獨立進程，每個進程有自己的 GIL，可實現真正並行。工具 (SpaCy NER, Regex) 可在 Worker Pool 中並行執行。 |
| 2025-12-05 | 使用 Rule-based Router 取代 LLM Router | Router 不需要 LLM，可以用規則判斷：(1) 若 tool 結果全為高信心結構化 PHI → tools_only；(2) 若文本含複雜指標 (罕見、遺傳等) → precise；(3) 其他 → fast。這樣避免額外的 LLM 調用開銷。 |
| 2025-12-05 | Safety Net Architecture - 移除 tools_only 路徑 | 發現致命盲點：如果任何節點漏檢且沒有後續核對，PHI 就會漏掉。解決方案：(1) 並行執行 Tools + LLM Agent；(2) 使用 UNION 合併結果，寧可誤報不可漏報；(3) 所有候選都必須經過 Verification Agent。移除危險的 tools_only 路徑。 |
| 2025-12-05 | Phase 1 必須包含完整 Agent 架構根基 | 速度太慢 = 沒人用的工具。Phase 1 不能只有 Tools，必須有 Single Agent + Tools 的完整架構：(1) Tool Workers 並行處理 ~0.01s；(2) PHI Agent (Qwen-0.5B) 確認 + 補漏 ~0.3s；(3) 總計 ~0.31s/chunk，1GB 約 8.6 小時，比純 LLM 快 20 倍。 |
| 2025-12-05 | 基於現有 Chain 架構擴展，不重寫 PHIIdentificationChain | 經過程式碼分析，發現現有架構已經成熟：
1. `chains/processors.py` 有完整的 `identify_phi_structured()` 函數，可直接加入 `tool_results` 參數
2. `map_reduce.py` 已有 `merge_phi_results()` 可處理結果合併
3. `PHIDetectionResponse` Pydantic model 設計良好，無需修改
4. 擴展比重寫更安全，不會破壞現有功能
5. 降低開發風險，可逐步增量發布 |
| 2025-12-05 | 採用 DSPy 進行自動 prompt 優化，整合到現有 LangChain Chain 架構中 | 1. DSPy 可自動生成 few-shot examples，減少手動 prompt engineering
2. 提供可量化的優化指標：F1 Score、Detection Time、Prompt Length
3. 與 LangChain 並存：DSPy 用於優化 prompt，LangChain 用於結構化輸出
4. 評估腳本提供完整混淆矩陣 (TP/FP/FN) 追蹤過度檢測和漏檢 |
| 2025-12-05 | Import PHIType from domain layer instead of redefining in tools module | DDD principle - domain types should only be defined in domain layer. Tools module is infrastructure layer and should import from domain. |
| 2025-12-05 | Implement Agent-based tool calling (PHIIdentificationAgent) where LLM decides when to use tools | Following ReAct pattern - LLM should decide intelligently when tools are needed based on text content, rather than always pre-scanning. This allows: 1) Skip unnecessary tool calls for simple texts, 2) LLM can request specific tools based on context, 3) Better integration of tool results with LLM reasoning. |
| 2025-12-05 | Implement FIFO stateless streaming architecture for unlimited file processing | User requirement to process arbitrarily large files without OOM. FIFO approach processes one chunk at a time, outputs immediately, releases memory. Checkpoint support enables resume after interruption. |
| 2025-12-06 | Use LangChain tools only for JSON parsing - no manual json.loads/re.search fallbacks | User explicitly requested: "json處理都用langchain我們自己寫也不會更完整(如果langchain fail就直接報錯!!)" - LangChain's with_structured_output and PydanticOutputParser should handle all JSON parsing. If they fail, report error rather than trying manual parsing which is error-prone. |
