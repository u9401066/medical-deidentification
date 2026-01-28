```skill
---
name: react-state
description: Zustand + Immer 狀態管理最佳實踐。Triggers: zustand, state, store, 狀態管理, immer.
---

# React State 狀態管理技能

## 描述

使用 Zustand + Immer 實現現代化的 React 狀態管理。

## 觸發條件

- 「zustand」「store」「狀態」
- 「state management」「狀態管理」
- 「immer」「不可變」

## 參照規範

- 子法：`.github/bylaws/frontend-ddd.md`

---

## 為什麼選擇 Zustand？

| 特點 | Zustand | Redux Toolkit | Context |
|------|---------|---------------|---------|
| Bundle Size | ~1KB | ~12KB | 0 (內建) |
| Boilerplate | 極少 | 中等 | 少 |
| 學習曲線 | 低 | 中 | 低 |
| DevTools | ✅ | ✅ | ❌ |
| 持久化 | 內建中介 | 需外掛 | 手動 |

---

## 基本使用

### 建立 Store

```typescript
// infrastructure/store/taskStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools, persist } from 'zustand/middleware';

interface Task {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'done' | 'error';
  progress: number;
}

interface TaskState {
  tasks: Task[];
  currentTaskId: string | null;
  
  // Actions
  addTask: (task: Task) => void;
  updateProgress: (id: string, progress: number) => void;
  setStatus: (id: string, status: Task['status']) => void;
  removeTask: (id: string) => void;
  reset: () => void;
}

const initialState = {
  tasks: [],
  currentTaskId: null,
};

export const useTaskStore = create<TaskState>()(
  devtools(
    persist(
      immer((set) => ({
        ...initialState,

        addTask: (task) =>
          set((state) => {
            state.tasks.push(task);
            state.currentTaskId = task.id;
          }),

        updateProgress: (id, progress) =>
          set((state) => {
            const task = state.tasks.find((t) => t.id === id);
            if (task) task.progress = progress;
          }),

        setStatus: (id, status) =>
          set((state) => {
            const task = state.tasks.find((t) => t.id === id);
            if (task) task.status = status;
          }),

        removeTask: (id) =>
          set((state) => {
            state.tasks = state.tasks.filter((t) => t.id !== id);
          }),

        reset: () => set(initialState),
      })),
      { name: 'task-storage' }
    ),
    { name: 'TaskStore' }
  )
);
```

### 在元件中使用

```typescript
// presentation/components/TaskList.tsx
import { useTaskStore } from '@/infrastructure/store/taskStore';

export function TaskList() {
  // 選擇性訂閱 (效能優化)
  const tasks = useTaskStore((state) => state.tasks);
  const addTask = useTaskStore((state) => state.addTask);

  return (
    <ul>
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </ul>
  );
}

// 使用 shallow 比較避免不必要的重渲染
import { shallow } from 'zustand/shallow';

function TaskSummary() {
  const { total, pending, done } = useTaskStore(
    (state) => ({
      total: state.tasks.length,
      pending: state.tasks.filter((t) => t.status === 'pending').length,
      done: state.tasks.filter((t) => t.status === 'done').length,
    }),
    shallow
  );

  return <div>Total: {total}, Pending: {pending}, Done: {done}</div>;
}
```

---

## 進階模式

### Slice 模式 (大型應用)

```typescript
// infrastructure/store/slices/uiSlice.ts
import { StateCreator } from 'zustand';

export interface UISlice {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const createUISlice: StateCreator<UISlice> = (set) => ({
  theme: 'light',
  sidebarOpen: true,
  toggleTheme: () =>
    set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
});

// infrastructure/store/index.ts
import { create } from 'zustand';
import { createUISlice, UISlice } from './slices/uiSlice';
import { createTaskSlice, TaskSlice } from './slices/taskSlice';

type AppStore = UISlice & TaskSlice;

export const useAppStore = create<AppStore>()((...a) => ({
  ...createUISlice(...a),
  ...createTaskSlice(...a),
}));
```

### 非同步 Actions

```typescript
interface TaskState {
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
  
  fetchTasks: () => Promise<void>;
  submitTask: (file: File) => Promise<string>;
}

export const useTaskStore = create<TaskState>()(
  immer((set, get) => ({
    tasks: [],
    isLoading: false,
    error: null,

    fetchTasks: async () => {
      set({ isLoading: true, error: null });
      try {
        const response = await fetch('/api/tasks');
        const tasks = await response.json();
        set({ tasks, isLoading: false });
      } catch (error) {
        set({ error: (error as Error).message, isLoading: false });
      }
    },

    submitTask: async (file) => {
      set({ isLoading: true });
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/tasks', {
          method: 'POST',
          body: formData,
        });
        
        const newTask = await response.json();
        set((state) => {
          state.tasks.push(newTask);
          state.isLoading = false;
        });
        
        return newTask.id;
      } catch (error) {
        set({ error: (error as Error).message, isLoading: false });
        throw error;
      }
    },
  }))
);
```

---

## 與 React Query 協作

```typescript
// Zustand 處理 UI 狀態
const useUIStore = create<UIState>()((set) => ({
  selectedTaskId: null,
  filterStatus: 'all',
  setSelectedTask: (id) => set({ selectedTaskId: id }),
  setFilter: (status) => set({ filterStatus: status }),
}));

// React Query 處理 Server 狀態
function TaskList() {
  const filterStatus = useUIStore((s) => s.filterStatus);
  
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks', filterStatus],
    queryFn: () => fetchTasks(filterStatus),
  });

  if (isLoading) return <Spinner />;
  return <TaskListView tasks={tasks} />;
}
```

---

## 測試

```typescript
// tests/unit/store/taskStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useTaskStore } from '@/infrastructure/store/taskStore';

describe('TaskStore', () => {
  beforeEach(() => {
    // 重置 store
    useTaskStore.getState().reset();
  });

  it('should add a task', () => {
    const { addTask } = useTaskStore.getState();
    
    addTask({
      id: '1',
      name: 'Test Task',
      status: 'pending',
      progress: 0,
    });

    expect(useTaskStore.getState().tasks).toHaveLength(1);
    expect(useTaskStore.getState().currentTaskId).toBe('1');
  });

  it('should update progress', () => {
    const { addTask, updateProgress } = useTaskStore.getState();
    
    addTask({ id: '1', name: 'Test', status: 'processing', progress: 0 });
    updateProgress('1', 50);

    const task = useTaskStore.getState().tasks[0];
    expect(task.progress).toBe(50);
  });
});
```

---

## 檔案結構

```text
web/frontend/src/
└── infrastructure/
    └── store/
        ├── index.ts            # 統一匯出
        ├── taskStore.ts        # 任務狀態
        ├── uiStore.ts          # UI 狀態
        └── slices/             # Slice 模式 (可選)
            ├── taskSlice.ts
            └── uiSlice.ts
```

---

## 檢查清單

建立 Store 時必須：

- [ ] 使用 TypeScript 定義完整的 State 介面
- [ ] 使用 Immer 處理不可變更新
- [ ] 配置 DevTools (開發模式)
- [ ] 考慮是否需要 Persist (持久化)
- [ ] 實作 reset 函數供測試使用
- [ ] 使用選擇性訂閱避免不必要重渲染

---

## 輸出格式

```text
🗃️ Zustand Store 建立完成

檔案：infrastructure/store/taskStore.ts

✅ 功能
  └─ 狀態：tasks, currentTaskId, isLoading, error
  └─ Actions：addTask, updateProgress, setStatus, removeTask
  └─ 中介：devtools, persist, immer

📦 安裝的套件
  └─ zustand: ^5.0.0
  └─ immer: ^10.0.0

🧪 測試建議
  └─ 建立 tests/unit/store/taskStore.test.ts
  └─ 測試每個 action 的狀態變化
```

```
