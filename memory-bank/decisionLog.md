# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-22 | 採用繁體中文及學術英文作為專案語言 | 確保團隊溝通清晰,同時維持技術文件的國際標準 |
| 2025-11-22 | 實施 GIT + MEM 同步原則 | 保持版本控制與知識管理一致性,確保專案脈絡可追溯 |
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
