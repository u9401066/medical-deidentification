# Progress (Updated: 2026-01-28)

## Done

- **任務處理 UX 強化** (2026-01-28)
  - ✅ AGE_OVER_89 hard rule - 過濾 LLM 誤判 (age < 89 排除)
  - ✅ Task 記憶持久化 (`tasks_db.json`)
  - ✅ 任務建立後立即顯示 (queryClient.setQueryData)
  - ✅ 自動切換到「任務」標籤頁
  - ✅ TaskCard 顯示原始檔名 (非 file_id)
  - ✅ uiStore 新增 activeTab 狀態管理
- **Web UI 系統維護功能** (2026-01-28)
  - ✅ 新增「系統維護」設定標籤頁
  - ✅ 清除 API: 上傳檔案/結果檔案/報告檔案/全部
  - ✅ 儲存空間統計顯示
  - ✅ PHI 設定重置為預設值功能
  - ✅ 確認刪除機制 (兩次點擊)
- **Web UI 改進** (2026-01-28)
  - ✅ 報告檔名顯示原始檔案名稱 (非 task_id)
  - ✅ PHI 識別結果修正: masked_value 正確顯示 [REDACTED]
  - ✅ Zustand + Immer 狀態管理 (uiStore, selectionStore)
  - ✅ React 進階 Skills (form, animation, patterns, testing, state)
  - ✅ ErrorBoundary 全域錯誤處理
  - ✅ 後端 API 日誌端點 (/api/logs)
  - ✅ Checkbox UI 元件
- Refactor project structure: moved medical_deidentification to core
- Update all internal references to use core package
- Run ruff check --fix and ruff format for code quality
- Configure Git user identity (u9401066)
- **LLM Benchmark 完成** (2025-06-21)
  - 測試 6 個模型: phi4:14b, gemma3:27b, gpt-oss:20b, llama3.3:70b, llama3.1:8b, phi3:3.8b
  - 🏆 **簡單案例最佳**: phi4:14b (F1=97.3%)
  - 建立 Benchmark 腳本: `scripts/benchmark/llm_benchmark.py`
  - 建立結果報告: `docs/llm-benchmark-results-2025.md`
- **複雜擬真案例 Benchmark** (2025-06-21)
  - 使用 PHI 標記測試資料 (108 個 PHI，5 個複雜案例)
  - ⚠️ **重大發現**: 簡單案例高估模型能力！
  - 🏆 **複雜案例最佳**: llama3.3:70b (F1=92.0%)
  - 🥈 **次佳選擇**: gemma3:27b (F1=89.9%)
  - ❌ **phi4:14b 在複雜案例失效**: F1 從 97% 降至 33%
- **Frontend DDD 架構規劃** (2026-01-14)
  - 創建子法: `.github/bylaws/frontend-ddd.md`
  - 更新憲法: 添加第 3.1 條前端 DDD 特別規範
  - 新增 Skill: `frontend-ddd` (前端架構輔助)
  - 更新 Skill: `test-generator` (支援 Vitest + RTL)
- **Frontend DDD 架構遷移完成** (2026-01-14)
  - ✅ 創建 DDD 目錄結構: domain/, application/, infrastructure/, presentation/, shared/
  - ✅ Domain 層: Task.ts, File.ts, Report.ts (entities) + PHIConfig.ts, PHIType.ts (value-objects)
  - ✅ Infrastructure 層: logger.ts (支援 Agent 讀取), api/client.ts, tasks.ts, files.ts
  - ✅ Application 層: useTasks.ts, useFiles.ts (React Query hooks)
  - ✅ Presentation 層: 從 components/ 複製所有 UI 元件
  - ✅ Shared 層: types/, utils/, constants/
  - ✅ 創建並修復 lib/utils.ts (向後兼容 cn, formatBytes, formatDate)
  - ✅ 修復 getFileExtension 邏輯錯誤
  - ✅ **68 個測試全部通過**
  - 📊 覆蓋率: domain=100%, infrastructure=89%, lib=90%
- **Frontend DDD 完全遷移** (2026-01-14)
  - ✅ 更新所有 presentation 元件 imports 到 `@/infrastructure/api` 和 `@/presentation/components/ui`
  - ✅ 更新 App.tsx imports 到 DDD 路徑
  - ✅ 刪除舊的 `api/` 和 `components/` 目錄
  - ✅ 遷移測試檔案到 DDD 層對應位置
  - ✅ **68 個測試全部通過**
  - 📊 最終目錄結構：
    ```
    src/
    ├── domain/          # 領域層 (100% 覆蓋)
    ├── application/     # 應用層
    ├── infrastructure/  # 基礎設施層 (89% 覆蓋)
    ├── presentation/    # 呈現層 (33% 覆蓋)
    ├── shared/          # 共享工具
    └── lib/             # 向後兼容 (90% 覆蓋)
    ```
- **Backend 模組化重構完成** (2026-01-14)
  - ✅ 從單體 main.py (1258 行) 拆分為模組化架構
  - ✅ 目錄結構:
    ```
    web/backend/
    ├── main.py          # 60 行 (入口)
    ├── config.py        # 配置
    ├── models/          # Pydantic 模型
    │   ├── config.py    # PHIConfig, PHITypeConfig
    │   ├── task.py      # TaskStatus, ProcessRequest
    │   ├── file.py      # UploadedFile
    │   └── regulation.py
    ├── services/        # 業務邏輯 (Singleton)
    │   ├── task_service.py
    │   ├── file_service.py
    │   ├── processing_service.py
    │   └── regulation_service.py
    └── api/             # FastAPI Routers
        ├── files.py, preview.py, processing.py
        ├── results.py, settings.py, health.py
        └── __init__.py (api_router 聚合器)
    ```
  - ✅ 所有 21 個 API 端點正常運作
  - ✅ 原始程式碼保留為 `main_legacy.py`
  - 📊 程式碼精簡: 1258 行 → 60 行 (入口), 總體更好維護
- **PHI 設定獨立服務** (2026-01-14)
  - ✅ 建立 `services/phi_config_service.py` - 獨立管理 PHI 設定
  - ✅ 設定持久化到 `data/phi_configs/current_config.json`
  - ✅ 支援設定導入/導出 (JSON 格式)
  - ✅ 內建 3 個預設範本 (HIPAA 標準、最小化、研究安全模式)
  - ✅ 新增 API 端點:
    - `GET/PUT /api/settings/config` - 取得/更新設定
    - `GET/PUT /api/settings/phi-types/{type}` - 個別類型設定
    - `GET /api/settings/export` - 導出設定 JSON
    - `GET /api/settings/export/download` - 下載設定檔
    - `POST /api/settings/import` - 上傳導入設定
    - `POST /api/settings/import/json` - JSON 導入設定
    - `GET/POST/DELETE /api/settings/presets/*` - 預設範本管理

## Doing

- 無

## Next

- 檢查系統維護功能是否正常
- 提升 Presentation 層測試覆蓋率到 70%
- E2E testing with Playwright
- Deployment documentation update
