/**
 * useTasks Hook - 任務管理 Hook
 *
 * 提供任務列表查詢和狀態管理功能
 */
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { logger } from '@/infrastructure/logging';
import { listTasks, getTask, startProcessing, ProcessRequest } from '@/infrastructure/api/tasks';
import {
  Task,
  isTaskCompleted,
  isTaskProcessing,
  isTaskFailed,
} from '@/domain/entities/Task';

// Query Keys
export const TASKS_QUERY_KEY = ['tasks'] as const;
export const TASK_QUERY_KEY = (taskId: string) => ['tasks', taskId] as const;

/**
 * 取得所有任務列表
 */
export function useTasks(options?: { refetchInterval?: number }) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: TASKS_QUERY_KEY,
    queryFn: async () => {
      logger.debug('Fetching tasks');
      return listTasks();
    },
    refetchInterval: options?.refetchInterval ?? 2000, // 預設每 2 秒更新
  });

  // 刷新任務列表
  const refresh = () => {
    logger.info('Refreshing tasks');
    queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEY });
  };

  // 計算任務統計
  const tasks = query.data ?? [];
  const processingTasks = tasks.filter(isTaskProcessing);
  const completedTasks = tasks.filter(isTaskCompleted);
  const failedTasks = tasks.filter(isTaskFailed);

  return {
    tasks,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refresh,
    // 統計
    processingCount: processingTasks.length,
    completedCount: completedTasks.length,
    failedCount: failedTasks.length,
    processingTasks,
    completedTasks,
    failedTasks,
  };
}

/**
 * 取得單一任務詳情
 */
export function useTask(taskId: string) {
  return useQuery({
    queryKey: TASK_QUERY_KEY(taskId),
    queryFn: async () => {
      logger.debug('Fetching task', { taskId });
      return getTask(taskId);
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      // 任務完成或失敗後停止輪詢
      const task = query.state.data as Task | undefined;
      if (task && (isTaskCompleted(task) || isTaskFailed(task))) {
        return false;
      }
      return 2000;
    },
  });
}

/**
 * 開始處理任務 Mutation
 */
export function useStartProcessing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: ProcessRequest) => {
      logger.info('Starting processing', {
        fileCount: request.fileIds.length,
        jobName: request.jobName,
      });
      return startProcessing(request);
    },
    onSuccess: (task) => {
      logger.info('Processing started successfully', { taskId: task.id });
      // 刷新任務列表
      queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEY });
    },
    onError: (error) => {
      logger.error('Failed to start processing', { error: String(error) });
    },
  });
}

export default {
  useTasks,
  useTask,
  useStartProcessing,
};
