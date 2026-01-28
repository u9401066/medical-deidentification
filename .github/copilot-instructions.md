# Copilot 自定義指令

## 開發哲學 💡

> **「想要寫文件的時候，就更新 Memory Bank 吧！」**
>
> **「想要零散測試的時候，就寫測試檔案進 tests/ 資料夾吧！」**

## 法規遵循

你必須遵守以下法規層級：

1. **憲法**：`CONSTITUTION.md` - 最高原則
2. **子法**：`.github/bylaws/*.md` - 細則規範
3. **技能**：`.claude/skills/*/SKILL.md` - 操作程序

## 架構原則

- 採用 DDD (Domain-Driven Design)
- DAL (Data Access Layer) 必須獨立
- 參見子法：`.github/bylaws/ddd-architecture.md`

## Python 環境（uv 唯一）

- 本專案**只使用 uv** 管理 Python 套件
- **禁止使用 pip**（包括 `pip install`, `pip freeze` 等）
- 必須建立虛擬環境（禁止全域安裝）
- 共用專案根目錄的 `.venv`（web/backend 也使用根目錄 venv）
- 參見子法：`.github/bylaws/python-environment.md`

### 常用指令

```bash
# 安裝依賴
uv pip install <package>
uv pip install -e .

# 新增依賴到 pyproject.toml
uv add <package>

# 同步依賴
uv sync

# 執行腳本
uv run python script.py

# 啟動 web 後端（使用根目錄 venv）
cd web/backend
/path/to/project/.venv/bin/python -m uvicorn main:app --reload
# 或使用啟動腳本
./scripts/start-web.sh
```

## Memory Bank 同步

每次重要操作必須更新 Memory Bank：
- 參見子法：`.github/bylaws/memory-bank.md`
- 目錄：`memory-bank/`

## Git 工作流

提交前必須執行檢查清單：
- 參見子法：`.github/bylaws/git-workflow.md`
- 觸發 Skill：`git-precommit`

## 可用 Skills

| Skill | 用途 | 觸發詞 |
|-------|------|--------|
| `git-precommit` | Git 提交前編排器 | commit, 提交, push |
| `memory-updater` | Memory Bank 同步 | memory, 記憶, 進度 |
| `memory-checkpoint` | 記憶檢查點 | checkpoint, 存檔 |
| `readme-updater` | README 智能更新 | readme |
| `changelog-updater` | CHANGELOG 自動更新 | changelog |
| `roadmap-updater` | ROADMAP 狀態追蹤 | roadmap |
| `code-reviewer` | 程式碼審查 | review, CR |
| `test-generator` | 測試生成 (Python + Frontend) | test, 測試, vitest |
| `code-refactor` | 主動重構 | refactor, 重構 |
| `ddd-architect` | DDD 架構輔助 | DDD, 架構 |
| `frontend-ddd` | 前端 DDD 架構 | frontend, 前端, react, vitest |
| `react-state` | Zustand + Immer 狀態管理 | zustand, store, 狀態 |
| `react-form` | React Hook Form + Zod 表單 | form, 表單, validation, zod |
| `react-animation` | Framer Motion 動畫 | animation, 動畫, framer, motion |
| `react-patterns` | 進階元件模式 | pattern, compound, HOC, render props |
| `react-testing` | RTL + MSW + Vitest 測試 | testing, msw, mock, 單元測試 |

## 回應風格

- 使用繁體中文
- 提供清晰的步驟說明
- 引用相關法規條文

---

## LLM 連線設定

本專案使用 Ollama 作為 LLM 服務：

| 設定 | 值 | 說明 |
|------|------|------|
| **預設 Ollama URL** | `http://192.168.1.2:30133` | GPU 伺服器 |
| **預設模型** | `gemma3:27b` | 27B 參數 |
| **配置檔** | `web/backend/config.py` | |

### 環境變數覆蓋

```bash
# 如需連接不同 Ollama 實例
export OLLAMA_BASE_URL=http://192.168.1.2:30133
export OLLAMA_MODEL=gemma3:27b
```

### 本地測試（可用小模型）
```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=smollm2:360m
```

---

## Web 前端開發規範

### 狀態管理模式

1. **Server State**: 使用 TanStack Query（`useQuery`, `useMutation`）
2. **Client State**: 使用 Zustand + Immer（見 `infrastructure/store/`）
   - `uiStore`: UI 狀態（activeTab, sidebar, preferences）
   - `selectionStore`: 選擇狀態（selectedFileId, checkedFileIds）

### Store 使用範例

```typescript
// 從 store 取得狀態
import { useSelectedFileId, useSelectionActions } from '@/infrastructure/store'
import { useActiveTab, useUIActions } from '@/infrastructure/store'

function MyComponent() {
  const selectedFileId = useSelectedFileId()
  const { selectFile, toggleCheckFile, clearCheckedFiles } = useSelectionActions()
  
  // Tab 控制 (tasks | reports)
  const activeTab = useActiveTab()
  const { setActiveTab } = useUIActions()
  // ...
}
```

### 即時 UI 更新

使用 `queryClient.setQueryData` 實現立即更新（不等待 refetch）：
```typescript
import { useQueryClient } from '@tanstack/react-query'

const queryClient = useQueryClient()

// 立即更新任務列表快取
queryClient.setQueryData<TaskStatus[]>(['tasks'], (old = []) => [newTask, ...old])

// 然後才 invalidate
queryClient.invalidateQueries({ queryKey: ['tasks'] })
```

### Toast 通知

使用 `sonner` 進行 Toast 通知：
```typescript
import { toast } from 'sonner'

// 在 mutation callbacks 中使用
onSuccess: () => toast.success('操作成功')
onError: () => toast.error('操作失敗')
```

### API 模組設計

- `api/index.ts`: Presentation 層使用的扁平 API
- `api/tasks.ts`: Application 層使用的 Domain-oriented API
- 兩者分離是刻意設計，勿合併

### UI 元件庫

使用 Radix UI + Tailwind 封裝的元件（見 `presentation/components/ui/`）：
- Button, Card, Badge, Tabs, Select, Switch, Checkbox, Table, ScrollArea 等
- 新增 UI 元件時需匯出到 `ui/index.ts`

### 測試規範

- 使用 Vitest + RTL + MSW
- Mock 檔案放在 `__mocks__/` 目錄
- 執行測試：`npm run test:run`

---

## PHI 處理 Hard Rules

### AGE_OVER_89 規則

LLM (gemma3:27b) 常將任意數字誤判為年齡，需後處理過濾：

```python
# web/backend/services/processing_service.py

def _apply_hard_rules(entities: list) -> list:
    """過濾 LLM 誤判"""
    filtered = []
    for entity in entities:
        if entity["phi_type"] == "AGE_OVER_89":
            age = extract_age_value(entity["original_value"])
            if age is None or age < 89:
                continue  # 排除年齡 < 89 的誤判
        filtered.append(entity)
    return filtered
```

### Task 持久化

任務狀態保存到 `web/backend/data/tasks_db.json`：
```python
# web/backend/config.py
TASKS_DB_FILE = DATA_DIR / "tasks_db.json"

# web/backend/services/task_service.py
def _load_tasks() -> dict
def _save_tasks() -> None
```

---

## 系統維護 API

### 清除資料 API

| Endpoint | Method | 說明 |
|----------|--------|------|
| `/api/cleanup/uploads` | DELETE | 清除所有上傳檔案 |
| `/api/cleanup/results` | DELETE | 清除所有結果檔案 |
| `/api/cleanup/reports` | DELETE | 清除所有報告檔案 |
| `/api/cleanup/all` | DELETE | 清除全部資料 + 任務 |
| `/api/cleanup/stats` | GET | 取得儲存空間統計 |

### 設定重置 API

| Endpoint | Method | 說明 |
|----------|--------|------|
| `/api/settings/reset` | POST | 重置 PHI 設定為預設值 |
| `/api/settings/default` | GET | 取得預設設定 (不修改) |

### PHI 設定預設值

```python
# 預設遮罩類型
masking_type = "redact"  # 顯示 [REDACTED]

# 預設 PHI 類型
phi_types = ["NAME", "DATE", "PHONE", "EMAIL", "ADDRESS", "ID_NUMBER", "MEDICAL_RECORD"]

# 保留格式
preserve_format = True
```

---

## MCP Servers (研究工具)

### Zotero Keeper
管理 Zotero 書目庫：文獻搜尋、PubMed 匯入、Collection 管理

### PubMed Search
搜尋醫學文獻：PICO 策略、引用分析、全文連結

### 核心流程
1. 搜尋：`parse_pico` → `generate_search_queries` → `search_literature`
2. 匯入：`list_collections` → 詢問用戶 → `batch_import_from_pubmed`
3. 避免重複：`search_pubmed_exclude_owned`
