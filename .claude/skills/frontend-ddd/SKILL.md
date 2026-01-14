---
name: frontend-ddd
description: Assist with Frontend DDD architecture design, component organization, and testing. Triggers: frontend, 前端, react, component, 元件, vitest.
---

# Frontend DDD 架構技能

## 描述

輔助 Frontend DDD 架構設計、元件組織和測試配置。

## 觸發條件

- 「frontend」「前端」「react」
- 「component」「元件」
- 「vitest」「前端測試」

## 參照規範

- 憲法：`CONSTITUTION.md` 第 3.1 條
- 子法：`.github/bylaws/frontend-ddd.md`

---

## 架構概覽

```text
web/frontend/src/
├── domain/              # 領域層（核心業務邏輯）
│   ├── entities/        # Task, File, Report
│   ├── value-objects/   # PHIConfig, MaskingType
│   └── events/          # 領域事件
│
├── application/         # 應用層（Use Cases）
│   ├── hooks/           # useTasks, useFiles
│   └── services/        # TaskService
│
├── infrastructure/      # 基礎設施層
│   ├── api/             # API 客戶端
│   ├── storage/         # Local Storage
│   └── logging/         # 日誌系統
│
├── presentation/        # 呈現層
│   ├── components/      # UI 元件
│   ├── pages/           # 頁面
│   └── layouts/         # 佈局
│
└── shared/              # 共享工具
```

---

## 日誌系統 (Agent 可讀取)

### 日誌輸出要求

1. **終端可見**：開發模式下輸出到 console
2. **結構化**：JSON 格式便於解析
3. **可追蹤**：支援 Agent 讀取

### 日誌模組範例

```typescript
// infrastructure/logging/logger.ts
type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
}

const log = (level: LogLevel, message: string, context?: object): void => {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    context,
  };

  // 開發模式：輸出到 console (Agent 可讀取)
  if (import.meta.env.DEV) {
    const prefix = `[${level}]`;
    console.log(prefix, message, context ?? '');

    // 存儲到全域變數供 Agent 查詢
    window.__FRONTEND_LOGS__ = window.__FRONTEND_LOGS__ ?? [];
    window.__FRONTEND_LOGS__.push(entry);
  }
};

export const logger = {
  debug: (msg: string, ctx?: object) => log('DEBUG', msg, ctx),
  info: (msg: string, ctx?: object) => log('INFO', msg, ctx),
  warn: (msg: string, ctx?: object) => log('WARN', msg, ctx),
  error: (msg: string, ctx?: object) => log('ERROR', msg, ctx),
};
```

### Agent 讀取日誌

在瀏覽器 DevTools Console 執行：

```javascript
// 取得所有日誌
window.__FRONTEND_LOGS__

// 篩選錯誤
window.__FRONTEND_LOGS__.filter(l => l.level === 'ERROR')
```

---

## 測試配置

### Vitest 配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 測試 Setup

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

### Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test"
  }
}
```

---

## 元件建立檢查清單

建立新元件時必須：

- [ ] 確認所屬層級 (presentation/components)
- [ ] 遵循命名規範 (PascalCase)
- [ ] 建立對應測試檔案 (*.test.tsx)
- [ ] 使用 logger 記錄關鍵操作
- [ ] 檔案長度 < 150 行

---

## 輸出格式

```text
🏗️ Frontend DDD 架構檢查

目標：web/frontend/src/

✅ 架構符合規範
  └─ domain/ 層：3 個實體
  └─ application/ 層：5 個 Hooks
  └─ presentation/ 層：12 個元件

⚠️ 建議改進
  └─ TasksPanel.tsx (180 行) 超過建議上限，考慮拆分
  └─ 缺少 infrastructure/logging/ 模組

📋 測試覆蓋率
  └─ domain: 92%
  └─ application: 78%
  └─ presentation: 65%

下一步：建立 logging 模組並配置測試
```

