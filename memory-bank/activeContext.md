# Active Context

## Current Goals

- ✅ Frontend DDD 重構完成
- ✅ Backend 模組化重構完成
- ✅ Web UI 系統維護功能
- ✅ E2E 測試套件 (58 Playwright tests)
- ✅ Systemd 服務部署
- ✅ **DDD Hooks 遷移** — Presentation 元件改用 Application Hooks
- ✅ **Self-Update Skill** — 自主審計更新 Skills/Hooks/Instructions
- ✅ **Pre-commit hook 擴充** — 新增 Python ruff + pytest 檢查

## Current Session Focus (Feb 20, 2026)

### DDD Hooks 遷移完成
- 建立 4 個新 Application Hooks: useResults, useReports, useHealth, useDownload
- 遷移 6 個 Presentation 元件到 hooks 模式:
  - TasksPanel ✅ (完全遷移)
  - TaskCard ✅ (download mutation)
  - DataPreview ✅ (useFiles + useFilePreview)
  - ResultsPanel ✅ (useResults + useResultDetail)
  - Reports ✅ (useReports + useReportDetail + useExportReport)
  - Sidebar ✅ (useFiles + useUploadFile + useDeleteFile + useHealth)
- 所有 TS 編譯錯誤已修正 (Domain UploadedFile camelCase 適配)

### 自動化基礎設施更新
- 建立 `self-update` skill (`.claude/skills/self-update/SKILL.md`)
- 擴充 pre-commit hook (Python ruff + pytest + Memory Bank 提醒)
- 更新 `copilot-instructions.md` (新增 self-update skill + hooks 清單)
- 清理 Memory Bank (productContext 從 ~250 行精簡到 ~60 行, systemPatterns 從 376 行精簡到 ~70 行)

## Test Status

| Suite | Result |
|-------|--------|
| Frontend Unit (Vitest) | 89/89 ✅ |
| Frontend E2E (Playwright) | 58/58 ✅ |
| Backend (pytest) | 122/122 ✅ (7 integration skipped - no Ollama) |

## Current Blockers

- None ✅