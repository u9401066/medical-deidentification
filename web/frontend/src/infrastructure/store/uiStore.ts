/**
 * UI Store - 全域 UI 狀態管理
 *
 * 使用 Zustand + Immer 處理 UI 相關狀態
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export type Theme = 'light' | 'dark' | 'system';

export interface UIState {
  // 側邊欄狀態
  sidebarOpen: boolean;
  sidebarWidth: number;

  // 主題
  theme: Theme;

  // 通知
  notifications: Notification[];

  // Actions
  toggleSidebar: () => void;
  setSidebarWidth: (width: number) => void;
  setTheme: (theme: Theme) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  reset: () => void;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  timestamp: number;
  duration?: number; // 自動消失時間 (ms)
}

const initialState = {
  sidebarOpen: true,
  sidebarWidth: 280,
  theme: 'system' as Theme,
  notifications: [] as Notification[],
};

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      immer((set) => ({
        ...initialState,

        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),

        setSidebarWidth: (width) =>
          set((state) => {
            state.sidebarWidth = Math.max(200, Math.min(400, width));
          }),

        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),

        addNotification: (notification) =>
          set((state) => {
            const newNotification: Notification = {
              ...notification,
              id: crypto.randomUUID(),
              timestamp: Date.now(),
            };
            state.notifications.push(newNotification);
          }),

        removeNotification: (id) =>
          set((state) => {
            state.notifications = state.notifications.filter((n) => n.id !== id);
          }),

        clearNotifications: () =>
          set((state) => {
            state.notifications = [];
          }),

        reset: () => set(initialState),
      })),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          sidebarWidth: state.sidebarWidth,
          theme: state.theme,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);

export default useUIStore;
