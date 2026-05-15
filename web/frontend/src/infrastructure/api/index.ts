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
  filename?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  phi_found?: number;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  file_ids: string[];  // 處理的檔案 ID 列表
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
  file_results?: Record<string, FileResult>;
  current_file?: string;
}

export interface ProcessRequest {
  file_ids: string[];
  config?: PHIConfig;
  job_name?: string;
}

export interface PreviewData {
  type: 'tabular' | 'table' | 'text' | 'json';
  columns?: string[];
  data?: Record<string, unknown>[];
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
  job_name: string;
  files_count: number;
  filenames: string[];  // 處理的檔案名稱列表
  total_phi_found: number;
  phi_by_type: Record<string, number>;
  processed_at: string;
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
  llm?: {
    status: 'online' | 'offline' | 'timeout';
    model: string | null;
    provider: string;
    endpoint?: string;
  };
  engine_available?: boolean;
}

// LLM 設定類型
export interface LLMConfig {
  provider: string;
  base_url: string;
  model: string;
  api_key?: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
}

export interface LLMModel {
  name: string;
  size?: string;
  modified_at?: string;
  quantization?: string;
}

export interface LLMStatus {
  online: boolean;
  provider: string;
  endpoint: string;
  current_model?: string;
  available_models: LLMModel[];
  error?: string;
}

export interface LLMProvider {
  id: string;
  name: string;
  description: string;
  requires_api_key: boolean;
  default_url: string;
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
  taskId: string,
  fileType: 'result' | 'report' = 'result',
  format: 'xlsx' | 'csv' | 'json' = 'xlsx'
): Promise<Blob> => {
  const response = await apiClient.get(`/download/${taskId}`, {
    params: { file_type: fileType, format },
    responseType: 'blob',
  });
  return response.data;
};

export const downloadSingleFileResult = async (
  taskId: string,
  fileId: string,
  format: 'xlsx' | 'csv' | 'json' = 'xlsx'
): Promise<Blob> => {
  const response = await apiClient.get(`/download/${taskId}/file/${fileId}`, {
    params: { format },
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

export type ReportExportFormat = 'json' | 'csv' | 'markdown';

export const exportReport = async (
  taskId: string,
  format: ReportExportFormat = 'json'
): Promise<Blob> => {
  const response = await apiClient.get(`/reports/${taskId}/export`, {
    params: { format },
    responseType: 'blob',
  });
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
// LLM APIs
// ============================================================

export const getLLMStatus = async (): Promise<LLMStatus> => {
  const response = await apiClient.get('/llm/status');
  return response.data;
};

export const getLLMModels = async (): Promise<LLMModel[]> => {
  const response = await apiClient.get('/llm/models');
  return response.data;
};

export const getLLMConfig = async (): Promise<LLMConfig> => {
  const response = await apiClient.get('/llm/config');
  return response.data;
};

export const updateLLMConfig = async (
  config: Partial<LLMConfig>
): Promise<{ message: string; config: LLMConfig }> => {
  const response = await apiClient.put('/llm/config', config);
  return response.data;
};

export const setLLMModel = async (
  model: string
): Promise<{ message: string; config: LLMConfig }> => {
  const response = await apiClient.post('/llm/model', { model });
  return response.data;
};

export const testLLMConnection = async (): Promise<{
  success: boolean;
  error?: string;
  provider?: string;
  model?: string;
}> => {
  const response = await apiClient.post('/llm/test');
  return response.data;
};

export const getLLMProviders = async (): Promise<LLMProvider[]> => {
  const response = await apiClient.get('/llm/providers');
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
  downloadSingleFileResult,
  previewFile,
  startProcessing,
  listTasks,
  getTask,
  getResults,
  getResultDetail,
  getReport,
  listReports,
  exportReport,
  getPHITypes,
  getConfig,
  updateConfig,
  listRegulations,
  getRegulationContent,
  uploadRegulation,
  updateRegulation,
  healthCheck,
  // LLM APIs
  getLLMStatus,
  getLLMModels,
  getLLMConfig,
  updateLLMConfig,
  setLLMModel,
  testLLMConnection,
  getLLMProviders,
};

export default api;
