```skill
---
name: react-testing
description: React Testing Library + MSW + Vitest 進階測試策略。Triggers: testing, 測試, vitest, msw, mock, 單元測試, integration test.
---

# React Testing 進階測試技能

## 描述

使用 Vitest + React Testing Library + MSW 實現完整的前端測試策略。

## 觸發條件

- 「testing」「測試」「test」
- 「vitest」「msw」「mock」
- 「單元測試」「integration test」

## 參照規範

- 子法：`.github/bylaws/frontend-ddd.md`

---

## 測試金字塔

```text
        /\
       /  \     E2E Tests (Playwright)
      /----\    少量，驗證關鍵流程
     /      \
    /--------\   Integration Tests (MSW + RTL)
   /          \  驗證元件互動與 API 整合
  /------------\
 /              \ Unit Tests (Vitest)
/________________\ 大量，驗證獨立邏輯
```

---

## 專案設定

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
    include: ['**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
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
import { afterEach, beforeAll, afterAll } from 'vitest';
import { server } from './mocks/server';

// 啟動 MSW
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
```

---

## MSW Mock Server 設定

### Handler 定義

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse, delay } from 'msw';

// 模擬資料
const mockTasks = [
  { id: '1', name: 'Task 1', status: 'done', progress: 100 },
  { id: '2', name: 'Task 2', status: 'processing', progress: 50 },
];

export const handlers = [
  // GET /api/tasks
  http.get('/api/tasks', async () => {
    await delay(100); // 模擬網路延遲
    return HttpResponse.json(mockTasks);
  }),

  // GET /api/tasks/:id
  http.get('/api/tasks/:id', ({ params }) => {
    const task = mockTasks.find((t) => t.id === params.id);
    if (!task) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(task);
  }),

  // POST /api/tasks
  http.post('/api/tasks', async ({ request }) => {
    const body = await request.json();
    const newTask = {
      id: Date.now().toString(),
      status: 'pending',
      progress: 0,
      ...body,
    };
    return HttpResponse.json(newTask, { status: 201 });
  }),

  // DELETE /api/tasks/:id
  http.delete('/api/tasks/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // 模擬檔案上傳
  http.post('/api/upload', async ({ request }) => {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    return HttpResponse.json({
      id: Date.now().toString(),
      filename: file?.name ?? 'unknown',
      size: file?.size ?? 0,
    });
  }),
];
```

### Server 設定

```typescript
// src/test/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

---

## 測試模式

### 1. 元件單元測試

```typescript
// tests/unit/components/Button.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/presentation/components/Button';

describe('Button', () => {
  it('should render children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await userEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should show loading state', () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });
});
```

### 2. Hook 測試

```typescript
// tests/unit/hooks/useLocalStorage.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '@/application/hooks/useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return initial value when no stored value', () => {
    const { result } = renderHook(() => useLocalStorage('key', 'initial'));
    expect(result.current[0]).toBe('initial');
  });

  it('should return stored value', () => {
    localStorage.setItem('key', JSON.stringify('stored'));
    const { result } = renderHook(() => useLocalStorage('key', 'initial'));
    expect(result.current[0]).toBe('stored');
  });

  it('should update stored value', () => {
    const { result } = renderHook(() => useLocalStorage('key', 'initial'));

    act(() => {
      result.current[1]('updated');
    });

    expect(result.current[0]).toBe('updated');
    expect(JSON.parse(localStorage.getItem('key')!)).toBe('updated');
  });

  it('should remove value', () => {
    localStorage.setItem('key', JSON.stringify('value'));
    const { result } = renderHook(() => useLocalStorage('key', 'initial'));

    act(() => {
      result.current[2](); // removeValue
    });

    expect(result.current[0]).toBe('initial');
    expect(localStorage.getItem('key')).toBeNull();
  });
});
```

### 3. 整合測試 (with MSW)

```typescript
// tests/integration/TaskList.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { TaskList } from '@/presentation/pages/TaskList';

// 建立測試用 QueryClient
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('TaskList Integration', () => {
  it('should display tasks from API', async () => {
    renderWithProviders(<TaskList />);

    // 等待資料載入
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // 驗證資料顯示
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  it('should show error state on API failure', async () => {
    // 覆寫 handler 模擬錯誤
    server.use(
      http.get('/api/tasks', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    renderWithProviders(<TaskList />);

    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  it('should create new task', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TaskList />);

    // 等待初始載入
    await screen.findByText('Task 1');

    // 開啟新增對話框
    await user.click(screen.getByRole('button', { name: /new task/i }));

    // 填寫表單
    await user.type(screen.getByLabelText(/name/i), 'New Task');
    await user.click(screen.getByRole('button', { name: /create/i }));

    // 驗證新任務出現
    await waitFor(() => {
      expect(screen.getByText('New Task')).toBeInTheDocument();
    });
  });

  it('should delete task', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TaskList />);

    await screen.findByText('Task 1');

    // 點擊刪除按鈕
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await user.click(deleteButtons[0]);

    // 確認刪除
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    // 驗證任務消失
    await waitFor(() => {
      expect(screen.queryByText('Task 1')).not.toBeInTheDocument();
    });
  });
});
```

### 4. 表單測試

```typescript
// tests/integration/TaskConfigForm.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskConfigForm } from '@/presentation/components/forms/TaskConfigForm';

describe('TaskConfigForm', () => {
  it('should show validation errors for empty required fields', async () => {
    const onSubmit = vi.fn();
    render(<TaskConfigForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/required/i)).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('should submit valid form', async () => {
    const onSubmit = vi.fn();
    render(<TaskConfigForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/name/i), 'Test Task');
    await userEvent.selectOptions(screen.getByLabelText(/type/i), 'redact');
    await userEvent.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          taskName: 'Test Task',
          maskingType: 'redact',
        })
      );
    });
  });

  it('should show conditional field based on selection', async () => {
    render(<TaskConfigForm onSubmit={vi.fn()} />);

    // 選擇 replace 模式
    await userEvent.selectOptions(screen.getByLabelText(/type/i), 'replace');

    // 應該顯示替換文字輸入框
    expect(screen.getByLabelText(/replacement/i)).toBeInTheDocument();
  });
});
```

### 5. Store 測試 (Zustand)

```typescript
// tests/unit/store/taskStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useTaskStore } from '@/infrastructure/store/taskStore';

describe('TaskStore', () => {
  beforeEach(() => {
    useTaskStore.getState().reset();
  });

  it('should have correct initial state', () => {
    const state = useTaskStore.getState();
    expect(state.tasks).toEqual([]);
    expect(state.currentTaskId).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('should add task', () => {
    const { addTask } = useTaskStore.getState();
    
    addTask({
      id: '1',
      name: 'Test Task',
      status: 'pending',
      progress: 0,
    });

    const state = useTaskStore.getState();
    expect(state.tasks).toHaveLength(1);
    expect(state.tasks[0].name).toBe('Test Task');
    expect(state.currentTaskId).toBe('1');
  });

  it('should update progress', () => {
    const { addTask, updateProgress } = useTaskStore.getState();
    
    addTask({ id: '1', name: 'Task', status: 'processing', progress: 0 });
    updateProgress('1', 75);

    const task = useTaskStore.getState().tasks[0];
    expect(task.progress).toBe(75);
  });

  it('should remove task', () => {
    const { addTask, removeTask } = useTaskStore.getState();
    
    addTask({ id: '1', name: 'Task 1', status: 'done', progress: 100 });
    addTask({ id: '2', name: 'Task 2', status: 'pending', progress: 0 });
    
    removeTask('1');

    const state = useTaskStore.getState();
    expect(state.tasks).toHaveLength(1);
    expect(state.tasks[0].id).toBe('2');
  });
});
```

---

## 測試工具函數

```typescript
// src/test/utils.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

interface WrapperProps {
  children: React.ReactNode;
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoutes?: string[];
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    initialRoutes = ['/'],
    queryClient = createTestQueryClient(),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialRoutes}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// 等待所有 pending 的 queries 完成
export async function waitForQueries(queryClient: QueryClient) {
  await queryClient.isFetching();
}
```

---

## 測試最佳實踐

### Do ✅

```typescript
// 使用 getByRole 優先 (無障礙友善)
screen.getByRole('button', { name: /submit/i });

// 使用 findBy* 等待非同步內容
await screen.findByText('Loaded');

// 使用 userEvent 模擬真實互動
await userEvent.type(input, 'text');
await userEvent.click(button);

// 測試行為而非實作
expect(screen.getByText('Success')).toBeInTheDocument();
```

### Don't ❌

```typescript
// 避免使用 getByTestId (除非無法用 role/text)
screen.getByTestId('submit-button'); // ❌

// 避免測試內部狀態
expect(component.state.count).toBe(1); // ❌

// 避免用 container.querySelector
container.querySelector('.my-class'); // ❌

// 避免直接操作 DOM
fireEvent.click(button); // 用 userEvent 更好
```

---

## 檔案結構

```text
web/frontend/
├── src/
│   └── test/
│       ├── setup.ts           # 全域設定
│       ├── utils.tsx          # 測試工具函數
│       └── mocks/
│           ├── handlers.ts    # MSW handlers
│           └── server.ts      # MSW server
│
└── tests/
    ├── unit/
    │   ├── components/
    │   │   └── Button.test.tsx
    │   ├── hooks/
    │   │   └── useLocalStorage.test.ts
    │   └── store/
    │       └── taskStore.test.ts
    │
    └── integration/
        ├── TaskList.test.tsx
        └── TaskConfigForm.test.tsx
```

---

## 執行測試

```bash
# 執行所有測試
npm test

# Watch 模式
npm run test -- --watch

# 執行特定檔案
npm run test -- TaskList

# 產生覆蓋率報告
npm run test:coverage

# 開啟 UI 模式
npm run test:ui
```

---

## 檢查清單

撰寫測試時必須：

- [ ] 使用 getByRole 優先於其他查詢方式
- [ ] 使用 userEvent 模擬使用者互動
- [ ] 使用 MSW 模擬 API 而非直接 mock fetch
- [ ] 測試元件的行為而非實作細節
- [ ] 覆蓋主要使用場景和邊界情況
- [ ] 保持測試獨立，不依賴其他測試的狀態

---

## 輸出格式

```text
🧪 測試檔案建立完成

檔案：tests/integration/TaskList.test.tsx

✅ 測試案例
  └─ should display tasks from API
  └─ should show error state on API failure
  └─ should create new task
  └─ should delete task

📦 使用的工具
  └─ vitest: ^4.0.0
  └─ @testing-library/react: ^16.0.0
  └─ msw: ^2.0.0
  └─ @testing-library/user-event: ^14.0.0

📊 覆蓋率目標
  └─ statements: 70%
  └─ branches: 70%
  └─ functions: 70%
  └─ lines: 70%
```

```
