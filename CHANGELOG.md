# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **AGE_OVER_89 Hard Rule** - 後處理過濾 LLM 誤判（年齡 < 89 排除）
- **任務持久化** - 任務狀態保存到 `tasks_db.json`，重新整理不會遺失
- **即時任務顯示** - 使用 `queryClient.setQueryData` 立即更新 UI
- **Tab 自動切換** - 「開始處理」後自動切換到任務標籤
- **原始檔名顯示** - TaskCard 顯示原始檔名（非 file_id）
- **uiStore activeTab** - Zustand 管理主標籤狀態
- **系統維護功能** - Settings 新增「系統維護」標籤頁
  - 清除 API: 上傳檔案/結果檔案/報告檔案/全部
  - 儲存空間統計 (檔案數量、大小)
  - PHI 設定重置為預設值
  - 確認刪除機制 (兩次點擊確認)
- **Zustand + Immer 狀態管理** - uiStore, selectionStore
- **React 進階 Skills** - form, animation, patterns, testing, state
- **ErrorBoundary** - 全域錯誤處理元件
- **後端日誌 API** - `/api/logs` 端點
- **Checkbox UI 元件** - 新增 checkbox.tsx
- **Web 功能完善**
  - Backend: LLM 設定 API (`api/llm.py`) — 連線狀態、設定管理、模型列表、Provider 切換
  - Backend: LLM 配置服務 (`services/llm_config_service.py`) — Ollama/OpenAI/Azure
  - Backend: 結果/報告詳情 API (`api/results.py` 擴充) — PHI 統計、詳情檢視
  - Backend: 健康檢查改進 — 新增 LLM 連線狀態
  - Frontend: Settings 面板大幅擴充 (PHI 設定 / 法規管理 / LLM 設定 三分頁)
  - Frontend: Reports 報告選擇 + 詳情顯示
  - Frontend: ResultsPanel 結果列表 + 點擊查看詳情
  - Frontend: DataPreview 檔案預覽 + 欄位顯示
  - Frontend: Sidebar LLM 狀態指示器、檔案選取互動
  - Frontend: TasksPanel 進度條、耗時顯示
- **Playwright E2E 測試** — 58 個測試涵蓋所有前端頁面
  - 測試範疇: 主佈局、側邊欄、任務面板、結果面板、報告面板、設定面板、資料預覽
  - Mock API 攔截 (`e2e/fixtures.ts`) 保證測試穩定性
  - Git pre-commit hook: 前端變更自動跑 Vitest + Playwright
- **Systemd 部署腳本** (`scripts/services/`)
  - 一鍵安裝/卸載前後端系統服務
  - Backend: uvicorn :8000 | Frontend: npm dev :5173

### Fixed
- 報告檔名顯示原始檔案名稱 (非 task_id)
- PHI 識別結果 masked_value 正確顯示 [REDACTED]

### Added
- **Frontend DDD Architecture** - 前端完全遷移到 Domain-Driven Design
  - Domain 層: Task, File, Report entities + PHIConfig, PHIType value-objects
  - Infrastructure 層: API 客戶端 + Logger (支援 Agent 讀取 `window.__FRONTEND_LOGS__`)
  - Application 層: React Query hooks (useTasks, useFiles)
  - Presentation 層: UI 元件遷移
  - Shared 層: 共享類型和工具
  - 68 個測試全部通過，domain 層 100% 覆蓋率
- **Frontend DDD 治理文件**
  - 子法: `.github/bylaws/frontend-ddd.md`
  - 新 Skill: `.claude/skills/frontend-ddd/SKILL.md`
  - 更新 `test-generator` 支援 Vitest + RTL
- **Lightweight LLM Benchmark & Recommendation** - CPU 環境輕量 LLM 效能評測
  - 🏆 `granite4:1b` - 最佳品質 (F1=89.4%, JSON 100% 成功)
  - ⭐ `qwen2.5:1.5b` - 最佳平衡 (F1=66.7%, 速度 ~4s)
  - `llama3.2:1b` - 高召回率 (79%) 但精確度較低
  - ❌ `smollm2:360m` - 太小無法理解 PHI 任務
- Benchmark script: `scripts/benchmark_lightweight_llms.py`
- DSPy 預設模型更新為 `granite4:1b`
- **MiniMind Ultra-Lightweight LLM Support** - 僅 26M-104M 參數的超輕量本地模型
  - `jingyaogong/minimind2` (104M, best performance)
  - `jingyaogong/minimind2-small` (26M, ultra-fast)
  - `jingyaogong/minimind2-r1` (R1-distilled reasoning)
- New LLM presets: `local_minimind()`, `local_minimind_small()`, `local_minimind_reasoning()`
- Comprehensive README with badges, quick start guide, and examples
- Detailed architecture documentation (DDD design patterns)
- Deployment guide with troubleshooting section
- Output directory structure: `data/output/results/`, `data/output/reports/`

### Changed
- Reorganized documentation structure under `docs/` folder
- Moved `OLLAMA_SETUP_GUIDE.md` to `docs/ollama-setup.md`
- Renamed `batch_processing.md` to `docs/batch-processing.md`
- Renamed `RAG_USAGE_GUIDE.md` to `docs/rag-usage.md`
- Updated output modules to infrastructure layer (DDD refactoring)

### Removed
- Outdated diagnostic reports (`ARCHITECTURE_FIX_STRATEGY_TYPE.md`, `CHAIN_DIAGNOSIS.md`)
- Old `STRUCTURE.md` (replaced by `docs/ARCHITECTURE.md`)

## [0.1.0-beta] - 2025-11-22

### Added
- Initial project structure with DDD architecture
- Core PHI identification using LLM (Ollama/OpenAI support)
- Batch processing for Excel files
- Token counting and performance statistics
- Support for 20+ PHI types (NAME, DATE, LOCATION, PHONE, etc.)
- Multi-language support (Traditional Chinese, English, Japanese, Korean, etc.)
- Customizable de-identification strategies
- RAG-based regulation context retrieval
- GPU acceleration support for Ollama
- Comprehensive documentation

### Fixed
- PHI detection response validation errors
- Automatic deduplication of identified entities
- Auto-calculation of total_entities count

[Unreleased]: https://github.com/u9401066/medical-deidentification/compare/v0.1.0-beta...HEAD
[0.1.0-beta]: https://github.com/u9401066/medical-deidentification/releases/tag/v0.1.0-beta
