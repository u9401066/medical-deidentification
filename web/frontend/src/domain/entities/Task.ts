/**
 * Task Entity - 處理任務實體
 *
 * 代表一個 PHI 去識別化處理任務
 */

export type TaskStatusType = 'pending' | 'processing' | 'completed' | 'failed';

export interface Task {
  readonly id: string;
  readonly status: TaskStatusType;
  readonly progress: number;
  readonly message: string;
  readonly createdAt: Date;
  readonly completedAt?: Date;
  readonly resultFile?: string;
  readonly reportFile?: string;
  // 計時相關
  readonly startedAt?: Date;
  readonly elapsedSeconds?: number;
  readonly estimatedRemainingSeconds?: number;
  readonly processingSpeed?: number; // chars per second
  readonly totalChars?: number;
  readonly processedChars?: number;
}

/**
 * 從 API 響應創建 Task 實體
 */
export function createTask(data: {
  task_id: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
  result_file?: string;
  report_file?: string;
  started_at?: string;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
  processing_speed?: number;
  total_chars?: number;
  processed_chars?: number;
}): Task {
  return {
    id: data.task_id,
    status: data.status as TaskStatusType,
    progress: data.progress,
    message: data.message,
    createdAt: new Date(data.created_at),
    completedAt: data.completed_at ? new Date(data.completed_at) : undefined,
    resultFile: data.result_file,
    reportFile: data.report_file,
    startedAt: data.started_at ? new Date(data.started_at) : undefined,
    elapsedSeconds: data.elapsed_seconds,
    estimatedRemainingSeconds: data.estimated_remaining_seconds,
    processingSpeed: data.processing_speed,
    totalChars: data.total_chars,
    processedChars: data.processed_chars,
  };
}

/**
 * 檢查任務是否完成
 */
export function isTaskCompleted(task: Task): boolean {
  return task.status === 'completed';
}

/**
 * 檢查任務是否失敗
 */
export function isTaskFailed(task: Task): boolean {
  return task.status === 'failed';
}

/**
 * 檢查任務是否處理中
 */
export function isTaskProcessing(task: Task): boolean {
  return task.status === 'processing';
}

/**
 * 格式化時間為人類可讀格式
 */
export function formatTaskTime(seconds?: number): string {
  if (seconds === undefined || seconds === null || seconds < 0) {
    return '計算中...';
  }
  if (seconds < 60) {
    return `${Math.round(seconds)} 秒`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins} 分 ${secs} 秒`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours} 小時 ${mins} 分`;
  }
}
