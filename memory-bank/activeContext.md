# Active Context

## Current Goals

- ✅ **Frontend DDD 重構完成** - 採用領域驅動設計重構 web/frontend
- ✅ 前端自動測試套件 (Vitest + React Testing Library)
- ✅ Log 輸出可讀取 (終端機 + Agent 可追蹤)
- ✅ **Backend 模組化重構完成** - 從單體拆分為 DDD 架構
- ✅ **Web UI 系統維護功能** - 清除資料、重置設定
- ✅ **任務處理 UX 強化** - 持久化、即時顯示、原始檔名
- ✅ **Structured Logging + PHI 同步問題修復** - 日誌系統 + 資料一致性
- ✅ **Web 功能完善** - LLM 設定、報告匯出、結果詳情、資料預覽
- ✅ **E2E 測試套件** - Playwright 58 個測試全部通過
- ✅ **Systemd 服務部署** - 一鍵安裝前後端服務

## Current Session Focus (Feb 20, 2026)

### Web 功能完善與 E2E 測試 ✅

#### Backend 新增功能
- **LLM 設定 API** (`api/llm.py` + `services/llm_config_service.py`)
  - LLM 連線狀態查詢、設定管理、模型列表
  - Provider 切換 (Ollama/OpenAI/Azure)
  - 連線測試功能
- **結果詳情 API** (`api/results.py` 擴充)
  - 報告列表、報告詳情、結果詳情
  - PHI 統計匯總
- **健康檢查改進** (`api/health.py`)
  - 新增 LLM 連線狀態

#### Frontend 完善功能
- **Settings 面板大幅擴充** - PHI 設定、法規管理、LLM 設定三分頁
- **Reports 面板** - Select 下拉選擇報告 + 詳情顯示
- **ResultsPanel** - 結果列表 + 點擊查看詳情
- **DataPreview** - 檔案預覽 + 欄位顯示
- **Sidebar** - LLM 狀態指示器、檔案選取互動
- **TasksPanel** - 進度條、耗時顯示

#### E2E 測試 (Playwright)
```
web/frontend/
├── playwright.config.ts     # Firefox + auto dev server
├── e2e/
│   ├── fixtures.ts          # 共用 mock + API 攔截
│   ├── app.spec.ts          # 主佈局 (7 tests)
│   ├── sidebar.spec.ts      # 側邊欄 (6 tests)
│   ├── tasks.spec.ts        # 任務面板 (6 tests)
│   ├── results.spec.ts      # 結果面板 (5 tests)
│   ├── reports.spec.ts      # 報告面板 (5 tests)
│   ├── settings.spec.ts     # 設定面板 (22 tests)
│   └── data-preview.spec.ts # 資料預覽 (4 tests)
└── package.json             # 新增 test:e2e scripts
```
- **58 個測試全部通過** (Firefox browser)
- Pre-commit hook: 前端變更時自動跑 Vitest + Playwright

#### Systemd 服務部署
```
scripts/services/
├── install-services.sh      # sudo 安裝服務
├── uninstall-services.sh    # 卸載服務
├── medical-deid-backend.service   # Backend (uvicorn :8000)
└── medical-deid-frontend.service  # Frontend (npm dev :5173)
```

## Current Blockers

- None ✅