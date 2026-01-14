/**
 * Tasks API - 任務相關 API
 */
import { apiClient } from './client';
import { logger } from '../logging';
import { Task, createTask } from '@/domain/entities/Task';
import { PHIConfig, toPHIConfigRequest } from '@/domain/value-objects/PHIConfig';

// API 響應類型
interface TaskStatusResponse {
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
}

export interface ProcessRequest {
  fileIds: string[];
  config?: PHIConfig;
  jobName?: string;
}

/**
 * 開始處理任務
 */
export async function startProcessing(request: ProcessRequest): Promise<Task> {
  logger.info('Starting processing task', {
    fileIds: request.fileIds,
    jobName: request.jobName,
  });

  const response = await apiClient.post<TaskStatusResponse>('/process', {
    file_ids: request.fileIds,
    config: request.config ? toPHIConfigRequest(request.config) : undefined,
    job_name: request.jobName,
  });

  const task = createTask(response.data);
  logger.info('Processing task created', { taskId: task.id });
  return task;
}

/**
 * 取得任務列表
 */
export async function listTasks(): Promise<Task[]> {
  logger.debug('Fetching task list');
  const response = await apiClient.get<TaskStatusResponse[]>('/tasks');
  return response.data.map(createTask);
}

/**
 * 取得單一任務
 */
export async function getTask(taskId: string): Promise<Task> {
  logger.debug('Fetching task', { taskId });
  const response = await apiClient.get<TaskStatusResponse>(`/tasks/${taskId}`);
  return createTask(response.data);
}

export default {
  startProcessing,
  listTasks,
  getTask,
};
