/**
 * Selection Store - 統一管理選中檔案狀態
 *
 * 用於 Sidebar、DataPreview、ResultsPanel 之間的連動
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { logger } from '../logging';

interface SelectionState {
  // 當前選中的檔案 ID（用於預覽/結果連動）
  selectedFileId: string | null;

  // 勾選的檔案 IDs（用於批次處理）
  checkedFileIds: string[];

  // 當前選中的結果任務 ID
  selectedResultTaskId: string | null;
}

interface SelectionActions {
  // 選擇檔案（單擊）- 連動預覽/結果
  selectFile: (fileId: string | null) => void;

  // 勾選/取消勾選檔案（用於批次處理）
  toggleCheckFile: (fileId: string) => void;

  // 批次勾選
  checkFiles: (fileIds: string[]) => void;

  // 清除所有勾選
  clearCheckedFiles: () => void;

  // 選擇結果任務
  selectResultTask: (taskId: string | null) => void;

  // 重置所有選取狀態
  reset: () => void;
}

const initialState: SelectionState = {
  selectedFileId: null,
  checkedFileIds: [],
  selectedResultTaskId: null,
};

export const useSelectionStore = create<SelectionState & SelectionActions>()(
  devtools(
    immer((set) => ({
      ...initialState,

      selectFile: (fileId) => {
        set((state) => {
          state.selectedFileId = fileId;
        });
        logger.debug('File selected', { fileId });
      },

      toggleCheckFile: (fileId) => {
        set((state) => {
          const index = state.checkedFileIds.indexOf(fileId);
          if (index >= 0) {
            state.checkedFileIds.splice(index, 1);
          } else {
            state.checkedFileIds.push(fileId);
          }
        });
        logger.debug('File check toggled', { fileId });
      },

      checkFiles: (fileIds) => {
        set((state) => {
          state.checkedFileIds = fileIds;
        });
        logger.debug('Files checked', { count: fileIds.length });
      },

      clearCheckedFiles: () => {
        set((state) => {
          state.checkedFileIds = [];
        });
        logger.debug('Checked files cleared');
      },

      selectResultTask: (taskId) => {
        set((state) => {
          state.selectedResultTaskId = taskId;
        });
        logger.debug('Result task selected', { taskId });
      },

      reset: () => {
        set(initialState);
        logger.debug('Selection state reset');
      },
    })),
    { name: 'selection-store' }
  )
);

// Selector hooks for optimized re-renders
export const useSelectedFileId = () =>
  useSelectionStore((state) => state.selectedFileId);

export const useCheckedFileIds = () =>
  useSelectionStore((state) => state.checkedFileIds);

export const useSelectedResultTaskId = () =>
  useSelectionStore((state) => state.selectedResultTaskId);

// Actions object - created once, stable reference
const selectionActions = {
  selectFile: (fileId: string | null) => useSelectionStore.getState().selectFile(fileId),
  toggleCheckFile: (fileId: string) => useSelectionStore.getState().toggleCheckFile(fileId),
  checkFiles: (fileIds: string[]) => useSelectionStore.getState().checkFiles(fileIds),
  clearCheckedFiles: () => useSelectionStore.getState().clearCheckedFiles(),
  selectResultTask: (taskId: string | null) => useSelectionStore.getState().selectResultTask(taskId),
  reset: () => useSelectionStore.getState().reset(),
};

// Returns stable action references to prevent infinite loops
export const useSelectionActions = () => selectionActions;
