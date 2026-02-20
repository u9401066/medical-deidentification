---
name: self-update
description: Audit and auto-update skills, hooks, instructions, and bylaws to stay in sync with codebase changes. Triggers: self-update, 自主更新, audit skills, 審計技能, update instructions, 更新指令, sync hooks, 同步 hooks.
---

# 自主更新技能 (Self-Update Skill)

## 描述

審計並自動更新專案的自動化基礎設施（Skills、Hooks、Instructions、Bylaws），確保與程式碼變更同步。

## 觸發條件

- 「self-update」「自主更新」「審計 skills」
- 新增/刪除前端元件或 API 端點後
- 架構模式變更後
- 每次 git commit 前（由 git-precommit 選擇性觸發）

## 審計範圍

### 1. Application Hooks 審計

檢查每個 `@/infrastructure/api` 匯出的功能是否有對應的 Application Hook：

```
掃描 web/frontend/src/infrastructure/api/index.ts 匯出清單
   ↓
對比 web/frontend/src/application/hooks/ 中已有的 hook
   ↓
列出缺少 hook 封裝的 API 功能
   ↓
自動建立缺少的 hook（使用 useQuery/useMutation 模式）
```

**Hook 命名規則：**
- 查詢：`use{ResourcePlural}()` → 回傳 `{ data, isLoading, error, refetch }`
- 單一：`use{Resource}Detail(id)` → 回傳 query result
- 變更：`use{Action}{Resource}()` → 回傳 `useMutation` result
- 查詢 key：`{RESOURCE}_QUERY_KEY`

### 2. Presentation 層 DDD 合規審計

檢查 `web/frontend/src/presentation/` 是否有直接引用 `@/infrastructure/`：

```bash
# 違規模式（應報告）
import api from '@/infrastructure/api'
import { someFunction } from '@/infrastructure/api'

# 合規模式（允許）
import type { SomeType } from '@/infrastructure/api'  # type-only OK
import { useXxx } from '@/application/hooks'           # 透過 hooks 層
```

### 3. Skills 清單同步

確保 `copilot-instructions.md` 中的 Skills 表格與 `.claude/skills/` 目錄一致：

```
掃描 .claude/skills/*/SKILL.md 的 name + description
   ↓
對比 .github/copilot-instructions.md 中的 Skills 表格
   ↓
自動更新表格（新增/移除項目）
```

### 4. API 端點同步

確保前端 API 模組與後端路由一致：

```
掃描 web/backend/routers/*.py 中的 @router 裝飾器
   ↓
對比 web/frontend/src/infrastructure/api/index.ts 中的函數
   ↓
列出缺少前端封裝的後端端點
```

### 5. Bylaws 合規檢查

驗證程式碼是否符合子法規範：

| 子法 | 檢查項目 |
|------|----------|
| `python-environment.md` | 無 pip 使用、使用 uv |
| `ddd-architecture.md` | 分層依賴方向正確 |
| `frontend-ddd.md` | Presentation 不直接引用 Infrastructure |
| `memory-bank.md` | Memory Bank 檔案存在且格式正確 |
| `git-workflow.md` | Commit message 格式 |

## 執行流程

```
┌─────────────────────────────────────────────────┐
│              Self-Update Orchestrator            │
├─────────────────────────────────────────────────┤
│  Step 1: audit-hooks      掃描 API → Hook 缺口  │
│  Step 2: audit-ddd        DDD 分層合規檢查       │
│  Step 3: audit-skills     Skills 清單同步        │
│  Step 4: audit-api        前後端 API 同步        │
│  Step 5: audit-bylaws     子法合規檢查           │
│  Step 6: auto-fix         自動修復可修復的問題    │
│  Step 7: report           產出審計報告           │
└─────────────────────────────────────────────────┘
```

## 自動修復能力

| 問題類型 | 自動修復 | 說明 |
|----------|----------|------|
| 缺少 Hook | ✅ | 自動建立 hook 檔案 |
| Skills 表格過期 | ✅ | 自動更新 copilot-instructions |
| Presentation 層違規 | ⚠️ | 提示 + 建議修復方式 |
| API 端點缺口 | ⚠️ | 提示 + 產出樣板 |
| 子法違規 | ❌ | 僅報告，需人工修復 |

## 輸出格式

```
🔄 Self-Update 審計報告

[1/5] Hook 審計
  ✅ 12/14 API 功能已有 Hook
  ⚠️ 缺少: useCleanup(), useSettings()
  🔧 已自動建立 2 個 Hook

[2/5] DDD 合規
  ✅ 8/10 元件合規
  ⚠️ 違規: DataPreview.tsx (直接 import api)
  💡 建議: 使用 useFilePreview hook

[3/5] Skills 清單
  ✅ 已同步 (17 skills)
  🔧 新增: self-update

[4/5] API 同步
  ✅ 前後端一致

[5/5] Bylaws 合規
  ✅ python-environment: 通過
  ✅ frontend-ddd: 2 項待修
  ✅ memory-bank: 通過

📊 總結: 2 項自動修復, 2 項需人工處理
🕐 審計時間: 2025-01-XX HH:MM
```

## 與其他 Skills 的關係

- **git-precommit**: commit 前可選擇性觸發 self-update 審計
- **memory-updater**: 審計結果記錄到 Memory Bank
- **code-reviewer**: 審計中的 DDD 合規檢查共用邏輯
- **ddd-architect**: 架構決策參考審計報告
