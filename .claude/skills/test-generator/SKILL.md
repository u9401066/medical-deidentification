---
name: test-generator
description: Generate test files for new code including unit, integration, and e2e tests. Triggers: test, 產生測試, generate test, 測試, 寫測試.
---

# 測試生成技能

## 描述

為新程式碼自動產生測試檔案，支援 **Python (pytest)** 和 **TypeScript/React (Vitest + RTL)**。

## 觸發條件

- 「generate tests」「產生測試」「寫測試」
- 新增功能後

---

## Python 測試

### 測試類型

#### Unit Tests（單元測試）

- 位置：`tests/unit/`
- 測試單一函數/類別
- Mock 外部依賴

#### Integration Tests（整合測試）

- 位置：`tests/integration/`
- 測試模組間互動
- 使用真實依賴（測試資料庫等）

#### E2E Tests（端到端測試）

- 位置：`tests/e2e/`
- 測試完整使用者流程

### 命名規範

```text
test_{module_name}.py
  └─ test_{function_name}_{scenario}
  └─ test_{function_name}_when_{condition}
```

### 執行命令

```bash
# 執行所有測試
uv run pytest

# 執行特定測試
uv run pytest tests/unit/test_phi_types.py -v
```

---

## Frontend 測試 (TypeScript/React)

> 依據子法：`.github/bylaws/frontend-ddd.md` 第 4 條

### 測試框架

| 類型 | 框架 | 用途 |
|------|------|------|
| 單元測試 | Vitest | 純函數、Hooks |
| 元件測試 | React Testing Library | UI 互動 |
| E2E 測試 | Playwright | 完整流程 |

### 測試位置

```text
web/frontend/
├── src/**/*.test.ts      # 元件旁測試（推薦）
└── tests/
    ├── unit/             # domain 層測試
    ├── integration/      # application 層測試
    └── e2e/              # 端到端測試
```

### 命名規範

```text
{ComponentName}.test.tsx
  └─ describe('{ComponentName}')
      └─ it('should {expected behavior}')
      └─ it('should {behavior} when {condition}')
```

### 測試範例

```typescript
// TasksPanel.test.tsx
import { render, screen } from '@testing-library/react';
import { TasksPanel } from './TasksPanel';

describe('TasksPanel', () => {
  it('should render task list', () => {
    render(<TasksPanel />);
    expect(screen.getByRole('list')).toBeInTheDocument();
  });

  it('should show empty state when no tasks', () => {
    render(<TasksPanel tasks={[]} />);
    expect(screen.getByText(/no tasks/i)).toBeInTheDocument();
  });
});
```

### 執行命令

```bash
cd web/frontend

# 執行所有測試
npm run test

# 監聽模式
npm run test:watch

# 覆蓋率報告
npm run test:coverage

# E2E 測試
npm run test:e2e
```

### 覆蓋率要求

| 層級 | 最低覆蓋率 |
|------|------------|
| domain | 90% |
| application | 80% |
| presentation | 70% |
| infrastructure | 60% |

---

## 輸出格式

### Python 測試輸出

```text
🧪 測試生成

目標：core/domain/phi_types.py

產生的測試檔案：
  ✅ tests/unit/test_phi_types.py
    └─ test_phi_type_validation
    └─ test_phi_type_from_string
    └─ test_phi_type_invalid_input

  ✅ tests/integration/test_phi_detection.py
    └─ test_detect_phi_in_text
    └─ test_detect_multiple_phi_types

測試覆蓋率預估：85%

下一步：執行 `uv run pytest tests/unit/test_phi_types.py -v`
```

### Frontend 測試輸出

```text
🧪 測試生成

目標：web/frontend/src/presentation/components/TasksPanel.tsx

產生的測試檔案：
  ✅ TasksPanel.test.tsx (元件旁測試)
    └─ should render task list
    └─ should show loading state
    └─ should handle task click

  ✅ tests/integration/useTasks.test.ts
    └─ should fetch tasks on mount
    └─ should handle API errors

測試覆蓋率預估：75%

下一步：執行 `cd web/frontend && npm run test`
```

