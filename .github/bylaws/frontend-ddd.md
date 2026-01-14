# 子法：Frontend DDD 架構規範

> 父法：CONSTITUTION.md 第一章
> 適用範圍：`web/frontend/`

## 第 1 條：目錄結構

```text
web/frontend/src/
├── domain/              # 領域層（核心業務邏輯）
│   ├── entities/        # 實體
│   │   ├── Task.ts      # 任務實體
│   │   ├── File.ts      # 檔案實體
│   │   └── Report.ts    # 報告實體
│   ├── value-objects/   # 值物件
│   │   ├── PHIConfig.ts
│   │   └── MaskingType.ts
│   ├── events/          # 領域事件
│   │   └── TaskEvents.ts
│   └── index.ts         # 領域層匯出
│
├── application/         # 應用層（Use Cases）
│   ├── hooks/           # React Hooks（Use Cases 實現）
│   │   ├── useTasks.ts
│   │   ├── useFiles.ts
│   │   └── useReports.ts
│   ├── services/        # 應用服務
│   │   └── TaskService.ts
│   └── index.ts
│
├── infrastructure/      # 基礎設施層
│   ├── api/             # API 客戶端
│   │   ├── client.ts    # Axios/Fetch 配置
│   │   ├── tasks.ts     # 任務 API
│   │   └── files.ts     # 檔案 API
│   ├── storage/         # 本地儲存
│   │   └── localStorage.ts
│   ├── logging/         # 日誌系統
│   │   ├── logger.ts    # 主日誌模組
│   │   └── console-transport.ts  # 終端機輸出
│   └── index.ts
│
├── presentation/        # 呈現層
│   ├── components/      # UI 元件
│   │   ├── ui/          # 基礎 UI (Button, Card, etc.)
│   │   ├── features/    # 功能元件
│   │   └── index.ts
│   ├── pages/           # 頁面元件
│   │   └── index.ts
│   ├── layouts/         # 佈局元件
│   │   └── MainLayout.tsx
│   └── index.ts
│
└── shared/              # 共享工具
    ├── types/           # TypeScript 類型
    │   └── index.ts
    ├── utils/           # 工具函數
    │   └── index.ts
    └── constants/       # 常數定義
        └── index.ts
```

## 第 2 條：依賴方向

```text
presentation → application → domain
                    ↓
             infrastructure
```

### 2.1 依賴規則

| 層級 | 可依賴 | 禁止依賴 |
|------|--------|----------|
| domain | 無 | 所有外層 |
| application | domain | presentation, infrastructure (透過介面) |
| infrastructure | domain | presentation |
| presentation | application, shared | domain (直接), infrastructure (直接) |

### 2.2 跨層溝通

- **presentation → application**: 透過 React Hooks
- **application → infrastructure**: 透過依賴注入或 Context
- **infrastructure → domain**: 實作 domain 定義的介面

## 第 3 條：命名慣例

| 類型 | 命名規則 | 範例 |
|------|----------|------|
| Entity | PascalCase 名詞 | `Task`, `ProcessingFile` |
| Value Object | PascalCase 描述性 | `PHIConfig`, `MaskingOptions` |
| Hook | camelCase use 開頭 | `useTasks`, `useFileUpload` |
| Component | PascalCase | `TasksPanel`, `FilePreview` |
| Service | PascalCase + Service | `TaskService`, `FileService` |
| API | camelCase + Api | `tasksApi`, `filesApi` |

## 第 4 條：測試規範

### 4.1 測試框架

- **單元測試**: Vitest
- **元件測試**: React Testing Library
- **E2E 測試**: Playwright

### 4.2 測試目錄結構

```text
web/frontend/
├── src/
│   └── **/*.test.ts     # 元件旁測試（推薦）
└── tests/
    ├── unit/            # 純函數單元測試
    ├── integration/     # Hook + API 整合測試
    └── e2e/             # 端到端測試
```

### 4.3 測試覆蓋率要求

| 層級 | 最低覆蓋率 | 測試重點 |
|------|------------|----------|
| domain | 90% | 業務邏輯正確性 |
| application | 80% | Hook 狀態管理 |
| presentation | 70% | 使用者互動 |
| infrastructure | 60% | API 呼叫/錯誤處理 |

### 4.4 測試命令

```bash
# 執行所有測試
npm run test

# 監聽模式
npm run test:watch

# 覆蓋率報告
npm run test:coverage

# E2E 測試
npm run test:e2e
```

## 第 5 條：日誌規範

### 5.1 日誌系統要求

1. **可終端輸出**：Agent 可讀取日誌
2. **結構化日誌**：JSON 格式便於解析
3. **分級別**：DEBUG, INFO, WARN, ERROR

### 5.2 日誌模組實現

```typescript
// infrastructure/logging/logger.ts
export interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  context?: Record<string, unknown>;
}

export const logger = {
  debug: (msg: string, ctx?: object) => log('DEBUG', msg, ctx),
  info: (msg: string, ctx?: object) => log('INFO', msg, ctx),
  warn: (msg: string, ctx?: object) => log('WARN', msg, ctx),
  error: (msg: string, ctx?: object) => log('ERROR', msg, ctx),
};
```

### 5.3 終端輸出配置

日誌必須可以透過以下方式輸出到終端：

1. **開發模式**: `console.log` 直接輸出
2. **生產模式**: 可選 WebSocket 回傳到後端

```typescript
// 開發環境自動輸出到 console
if (import.meta.env.DEV) {
  window.__FRONTEND_LOGS__ = [];  // Agent 可讀取
}
```

## 第 6 條：模組化規範

> 依據憲法第 7.3 條「主動重構原則」訂定

### 6.1 檔案長度限制

| 類型 | 建議上限 | 硬性上限 |
|------|----------|----------|
| Component | 150 行 | 300 行 |
| Hook | 100 行 | 200 行 |
| Service | 150 行 | 300 行 |
| Entity | 50 行 | 100 行 |

### 6.2 元件拆分原則

- 單一職責：一個元件只做一件事
- 可測試性：複雜邏輯抽到 Hook
- 可重用性：通用 UI 放 `ui/` 目錄

---

## 附錄 A：遷移指南

### 從現有結構遷移

```bash
# 現有結構
src/
├── components/   → presentation/components/
├── api/          → infrastructure/api/

# 新增
├── domain/       # 全新建立
├── application/  # 從 components 抽取 hooks
```

### 遷移步驟

1. 建立新目錄結構
2. 抽取業務邏輯到 domain
3. 遷移 hooks 到 application
4. 遷移 components 到 presentation
5. 配置路徑別名

---

*本子法版本：v1.0.0*

