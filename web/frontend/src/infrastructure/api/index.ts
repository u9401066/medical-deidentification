/**
 * Infrastructure API - API 模組匯出
 *
 * 完整的 API 客戶端、類型定義和方法
 */

import axios from 'axios';
import { logger } from '../logging';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器
apiClient.interceptors.request.use(
  (config) => {
    logger.debug('API Request', {
      method: config.method?.toUpperCase(),
      url: config.url,
    });
    return config;
  },
  (error) => {
    logger.error('API Request Error', { error: error.message });
    return Promise.reject(error);
  }
);

// 響應攔截器
apiClient.interceptors.response.use(
  (response) => {
    logger.debug('API Response', {
      status: response.status,
      url: response.config.url,
    });
    return response;
  },
  (error) => {
    logger.error('API Response Error', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
    });
    return Promise.reject(error);
  }
);

// ============================================================
// Types
// ============================================================

export interface UploadedFile {
  id: string;
  file_id?: string;
  filename: string;
  size: number;
  upload_time: string;
  file_type: string;
  preview_available: boolean;
  status: 'pending' | 'processing' | 'completed' | 'error';
  task_id?: string | null;  // 關聯的處理任務 ID
}

export interface PHITypeConfig {
  enabled?: boolean;
  masking?: MaskingType;
  replace_with?: string;  // 自訂替換詞，當 masking 為 'replace' 時使用
}

export interface PHIConfig {
  enabled?: boolean;
  strict_mode?: boolean;
  default_masking?: MaskingType;
  masking_type?: string;
  phi_types?: Record<string, PHITypeConfig>;
  preserve_format?: boolean;
  custom_patterns?: Record<string, string>;
}

export interface FileResult {
  file_id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  phi_found: number;
  error?: string | null;
  processing_time?: number | null;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  file_ids?: string[];
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  result_file?: string;
  report_file?: string;
  started_at?: string;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
  processing_speed?: number;
  total_chars?: number;
  processed_chars?: number;
  // 單檔處理狀態
  file_results?: Record<string, FileResult>;
  current_file?: string;
  files_completed?: number;
  total_files?: number;
  elapsed_time?: number;
  elapsed_time_formatted?: string;
  estimated_remaining_formatted?: string;
}

export interface ProcessRequest {
  file_ids: string[];
  config?: PHIConfig;
  job_name?: string;
}

export interface PreviewData {
  type: 'tabular' | 'text' | 'json' | 'markdown';
  columns?: string[];
  data?: Record<string, unknown>[];
  source_format?: string;
  content?: string;
  lines?: string[];
  total_rows: number;
  total_lines?: number;
  total_items?: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface PHIType {
  type: string;
  display_name: string;
  description: string;
  category: string;
  default_masking?: string;
}

export type MaskingType = 'mask' | 'hash' | 'replace' | 'delete' | 'keep';

export interface RegulationRule {
  id: string;
  name: string;
  description: string;
  phi_types: string[];
  source: string;
  enabled: boolean;
  rules_count: number;
}

export interface RegulationContent {
  id: string;
  name: string;
  content: string;
  source_file?: string;
}

export interface Report {
  id: string;
  filename: string;
  task_id: string;
  job_name?: string;
  files_processed: number;
  total_phi_found: number;
  created_at: string;
  generated_at?: string;
}

export interface PHIEntity {
  type: string;
  value: string;
  masked_value: string;
  field?: string | null;
  row?: number | null;
  confidence?: number;
  start_pos?: number;
  end_pos?: number;
  reason?: string;
}

export interface ReportDetail {
  task_id: string;
  job_name?: string;
  generated_at?: string;
  summary?: {
    files_processed?: number;
    total_phi_found?: number;
    total_chars?: number;
    processing_time_seconds?: number;
    processing_speed_chars_per_sec?: number;
  };
  file_details?: Array<{
    file_id: string;
    filename: string;
    phi_found: number;
    phi_by_type?: Record<string, number>;
    rows_processed?: number;
    status: string;
    phi_entities?: PHIEntity[];
    original_data?: Record<string, unknown>[];
    masked_data?: Record<string, unknown>[] | null;
    original_content?: string;
    masked_content?: string;
  }>;
}

export interface ResultItem {
  task_id: string;
  filename: string;
  phi_count: number;
  status: string;
  created_at: string;
  results?: Array<{
    file_id: string;
    filename: string;
    phi_found: number;
    rows_processed?: number;
    status: string;
  }>;
}

export interface ResultDetail {
  task_id: string;
  job_name: string;
  config: {
    masking_type: string;
    phi_types: string[];
  };
  results: Array<{
    file_id: string;
    filename: string;
    phi_found: number;
    phi_by_type?: Record<string, number>;
    rows_processed?: number;
    status: string;
    phi_entities?: PHIEntity[];
    original_data?: Record<string, unknown>[];
    masked_data?: Record<string, unknown>[];
    original_content?: string;
    masked_content?: string;
    output_path?: string;
  }>;
  processed_at: string;
}

export interface HealthStatus {
  status: string;
  timestamp?: string;
  version?: string;
  llm?: {
    status: 'online' | 'offline' | 'model_not_found' | 'timeout';
    model: string | null;
    provider: string;
    endpoint?: string;
    available_models?: string[];
  };
  engine_available?: boolean;
}

export interface CleanupResult {
  success: boolean;
  message: string;
  files_deleted: number;
  bytes_freed: number;
}

export interface CleanupAllResult {
  uploads: CleanupResult;
  results: CleanupResult;
  reports: CleanupResult;
  tasks_cleared: number;
  total_bytes_freed: number;
}

export interface DirectoryStats {
  files_count: number;
  total_size: number;
}

export interface CleanupStats {
  uploads: DirectoryStats;
  results: DirectoryStats;
  reports: DirectoryStats;
  tasks: { count: number };
}

// ============================================================
// File APIs
// ============================================================

export const uploadFile = async (file: File): Promise<UploadedFile> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listFiles = async (): Promise<UploadedFile[]> => {
  const response = await apiClient.get('/files');
  return response.data.map((f: UploadedFile & { file_id?: string }) => ({
    ...f,
    id: f.file_id || f.id,
    status: f.status || 'pending',
    task_id: f.task_id || null,
  }));
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await apiClient.delete(`/files/${fileId}`);
};

export const downloadResult = async (
  fileId: string,
  fileType: 'result' | 'report' = 'result',
  format: 'xlsx' | 'csv' | 'json' = 'xlsx'
): Promise<Blob> => {
  const response = await apiClient.get(`/download/${fileId}`, {
    params: { file_type: fileType, format },
    responseType: 'blob',
  });
  return response.data;
};

// ============================================================
// Preview APIs
// ============================================================

export const previewFile = async (
  fileId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PreviewData> => {
  const response = await apiClient.get(`/preview/${fileId}`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

// ============================================================
// Processing APIs
// ============================================================

export const startProcessing = async (request: ProcessRequest): Promise<TaskStatus> => {
  const response = await apiClient.post('/process', request);
  return response.data;
};

export const listTasks = async (): Promise<TaskStatus[]> => {
  const response = await apiClient.get('/tasks');
  return response.data;
};

export const getTask = async (taskId: string): Promise<TaskStatus> => {
  const response = await apiClient.get(`/tasks/${taskId}`);
  return response.data;
};

// ============================================================
// Results & Reports APIs
// ============================================================

export const getResults = async (): Promise<ResultItem[]> => {
  const response = await apiClient.get(`/results`);
  return response.data;
};

export const getReport = async (taskId: string): Promise<ReportDetail> => {
  const response = await apiClient.get(`/reports/${taskId}`);
  return response.data;
};

export const getResultDetail = async (taskId: string): Promise<ResultDetail> => {
  const response = await apiClient.get(`/results/${taskId}`);
  return response.data;
};

export const listReports = async (): Promise<Report[]> => {
  const response = await apiClient.get('/reports');
  return response.data;
};

// ============================================================
// Settings APIs
// ============================================================

export const getPHITypes = async (): Promise<PHIType[]> => {
  const response = await apiClient.get('/settings/phi-types');
  return response.data.phi_types || response.data;
};

export const getConfig = async (): Promise<PHIConfig> => {
  const response = await apiClient.get('/settings/config');
  return response.data;
};

export const updateConfig = async (
  config: PHIConfig
): Promise<{ message: string; config: PHIConfig }> => {
  const response = await apiClient.put('/settings/config', config);
  return response.data;
};

// ============================================================
// Regulations APIs
// ============================================================

export const listRegulations = async (): Promise<RegulationRule[]> => {
  const response = await apiClient.get('/regulations');
  return response.data;
};

export const getRegulationContent = async (ruleId: string): Promise<RegulationContent> => {
  const response = await apiClient.get(`/regulations/${ruleId}/content`);
  return response.data;
};

export const uploadRegulation = async (
  file: File
): Promise<{ message: string; rules: RegulationRule[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/regulations/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateRegulation = async (
  ruleId: string,
  enabled: boolean
): Promise<{ message: string; rule_id: string; enabled: boolean }> => {
  const response = await apiClient.put(`/regulations/${ruleId}`, null, {
    params: { enabled },
  });
  return response.data;
};

// ============================================================
// Health Check
// ============================================================

export const healthCheck = async (): Promise<HealthStatus> => {
  const response = await apiClient.get('/health');
  return response.data;
};

// ============================================================
// Cleanup APIs (系統維護)
// ============================================================

export const cleanupUploads = async (): Promise<CleanupResult> => {
  const response = await apiClient.delete('/cleanup/uploads');
  return response.data;
};

export const cleanupResults = async (): Promise<CleanupResult> => {
  const response = await apiClient.delete('/cleanup/results');
  return response.data;
};

export const cleanupReports = async (): Promise<CleanupResult> => {
  const response = await apiClient.delete('/cleanup/reports');
  return response.data;
};

export const cleanupAll = async (): Promise<CleanupAllResult> => {
  const response = await apiClient.delete('/cleanup/all');
  return response.data;
};

export const getCleanupStats = async (): Promise<CleanupStats> => {
  const response = await apiClient.get('/cleanup/stats');
  return response.data;
};

// ============================================================
// Settings Reset API
// ============================================================

export const resetConfig = async (): Promise<{ message: string; config: PHIConfig }> => {
  const response = await apiClient.post('/settings/reset');
  return response.data;
};

export const getDefaultConfig = async (): Promise<PHIConfig> => {
  const response = await apiClient.get('/settings/default');
  return response.data;
};

// ============================================================
// Export all as a single object for convenience
// ============================================================

const api = {
  uploadFile,
  listFiles,
  deleteFile,
  downloadResult,
  previewFile,
  startProcessing,
  listTasks,
  getTask,
  getResults,
  getResultDetail,
  getReport,
  listReports,
  getPHITypes,
  getConfig,
  updateConfig,
  listRegulations,
  getRegulationContent,
  uploadRegulation,
  updateRegulation,
  healthCheck,
  // Cleanup & Reset
  cleanupUploads,
  cleanupResults,
  cleanupReports,
  cleanupAll,
  getCleanupStats,
  resetConfig,
  getDefaultConfig,
};

export default api;
