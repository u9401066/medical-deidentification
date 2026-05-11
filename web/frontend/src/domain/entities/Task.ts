/**
 * Task Entity - 處理任務實體
 *
 * 代表一個 PHI 去識別化處理任務
 */

export type TaskStatusType = 'pending' | 'processing' | 'completed' | 'completed_with_errors' | 'failed';
export type FileTaskStatusType = 'pending' | 'processing' | 'completed' | 'error';

export interface FileTaskResult {
  readonly fileId: string;
  readonly filename?: string;
  readonly status: FileTaskStatusType;
  readonly phiFound: number;
  readonly error?: string | null;
  readonly processingTime?: number | null;
}

export interface Task {
  readonly id: string;
  readonly status: TaskStatusType;
  readonly progress: number;
  readonly message: string;
  readonly fileIds: string[];
  readonly fileResults: Record<string, FileTaskResult>;
  readonly ownerUserId?: string | null;
  readonly ownerUsername?: string | null;
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
  readonly currentFile?: string | null;
  readonly filesCompleted?: number;
  readonly totalFiles?: number;
  readonly phase?: string | null;
  readonly phaseLabel?: string | null;
  readonly currentFileProgress?: number | null;
  readonly elapsedTimeFormatted?: string | null;
  readonly estimatedRemainingFormatted?: string | null;
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
  file_ids?: string[];
  file_results?: Record<string, {
    file_id: string;
    filename?: string;
    status: string;
    phi_found?: number;
    error?: string | null;
    processing_time?: number | null;
  }>;
  owner_user_id?: string | null;
  owner_username?: string | null;
  current_file?: string | null;
  files_completed?: number;
  total_files?: number;
  phase?: string | null;
  phase_label?: string | null;
  current_file_progress?: number | null;
  elapsed_time?: number;
  estimated_remaining?: number;
  elapsed_time_formatted?: string | null;
  estimated_remaining_formatted?: string | null;
}): Task {
  const fileResults = Object.fromEntries(
    Object.entries(data.file_results ?? {}).map(([fileId, result]) => [
      fileId,
      {
        fileId: result.file_id || fileId,
        filename: result.filename,
        status: result.status as FileTaskStatusType,
        phiFound: result.phi_found ?? 0,
        error: result.error,
        processingTime: result.processing_time,
      },
    ])
  );

  return {
    id: data.task_id,
    status: data.status as TaskStatusType,
    progress: data.progress,
    message: data.message,
    fileIds: data.file_ids ?? [],
    fileResults,
    ownerUserId: data.owner_user_id ?? null,
    ownerUsername: data.owner_username ?? null,
    createdAt: new Date(data.created_at),
    completedAt: data.completed_at ? new Date(data.completed_at) : undefined,
    resultFile: data.result_file,
    reportFile: data.report_file,
    startedAt: data.started_at ? new Date(data.started_at) : undefined,
    elapsedSeconds: data.elapsed_seconds ?? data.elapsed_time,
    estimatedRemainingSeconds: data.estimated_remaining_seconds ?? data.estimated_remaining,
    processingSpeed: data.processing_speed,
    totalChars: data.total_chars,
    processedChars: data.processed_chars,
    currentFile: data.current_file,
    filesCompleted: data.files_completed,
    totalFiles: data.total_files,
    phase: data.phase,
    phaseLabel: data.phase_label,
    currentFileProgress: data.current_file_progress,
    elapsedTimeFormatted: data.elapsed_time_formatted,
    estimatedRemainingFormatted: data.estimated_remaining_formatted,
  };
}

/**
 * 檢查任務是否完成
 */
export function isTaskCompleted(task: Task): boolean {
  return task.status === 'completed' || task.status === 'completed_with_errors';
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
