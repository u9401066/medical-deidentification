/**
 * Task Store - 任務相關狀態管理
 *
 * 管理本地任務狀態，與 React Query 的 server state 互補
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface LocalTask {
  id: string;
  filename: string;
  status: 'uploading' | 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
  createdAt: number;
}

export interface TaskState {
  // 本地任務追蹤 (上傳中、排隊中)
  localTasks: LocalTask[];
  
  // 當前選中的任務
  selectedTaskId: string | null;
  
  // 篩選狀態
  filterStatus: 'all' | 'processing' | 'completed' | 'failed';
  
  // Actions
  addLocalTask: (task: Omit<LocalTask, 'createdAt'>) => void;
  updateLocalTask: (id: string, updates: Partial<LocalTask>) => void;
  removeLocalTask: (id: string) => void;
  setSelectedTask: (id: string | null) => void;
  setFilterStatus: (status: TaskState['filterStatus']) => void;
  reset: () => void;
}

const initialState = {
  localTasks: [] as LocalTask[],
  selectedTaskId: null as string | null,
  filterStatus: 'all' as TaskState['filterStatus'],
};

export const useTaskStore = create<TaskState>()(
  devtools(
    immer((set) => ({
      ...initialState,

      addLocalTask: (task) =>
        set((state) => {
          state.localTasks.push({
            ...task,
            createdAt: Date.now(),
          });
        }),

      updateLocalTask: (id, updates) =>
        set((state) => {
          const task = state.localTasks.find((t) => t.id === id);
          if (task) {
            Object.assign(task, updates);
          }
        }),

      removeLocalTask: (id) =>
        set((state) => {
          state.localTasks = state.localTasks.filter((t) => t.id !== id);
        }),

      setSelectedTask: (id) =>
        set((state) => {
          state.selectedTaskId = id;
        }),

      setFilterStatus: (status) =>
        set((state) => {
          state.filterStatus = status;
        }),

      reset: () => set(initialState),
    })),
    { name: 'TaskStore' }
  )
);

export default useTaskStore;
