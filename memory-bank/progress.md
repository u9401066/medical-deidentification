# Progress (Updated: 2026-01-14)

## Done

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

## Doing

- 無

## Next

- 提升 Presentation 層測試覆蓋率到 70%
- E2E testing with Playwright
- Deployment documentation update
