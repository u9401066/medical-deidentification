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
}

export interface PHIConfig {
  enabled?: boolean;
  strict_mode?: boolean;
  default_masking?: MaskingType;
  masking_type?: string;
  phi_types?: Record<string, { enabled?: boolean; masking?: MaskingType }>;
  preserve_format?: boolean;
  custom_patterns?: Record<string, string>;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
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
  file_ids: string[];
  config?: PHIConfig;
  job_name?: string;
}

export interface PreviewData {
  type: 'tabular' | 'text' | 'json';
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

export interface ReportDetail {
  id: string;
  filename: string;
  source_file_id: string;
  created_at: string;
  task_id?: string;
  job_name?: string;
  summary?: {
    total_records?: number;
    phi_found?: number;
    phi_masked?: number;
    processing_time?: number;
    files_processed?: number;
  };
  phi_types?: Record<string, number>;
  details?: Array<{
    field: string;
    original: string;
    masked: string;
    phi_type: string;
  }>;
  file_details?: Array<{
    file_id: string;
    filename: string;
    phi_found: number;
    rows_processed?: number;
    status: string;
  }>;
  generated_at?: string;
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

export interface PHIEntity {
  type: string;
  value: string;
  masked_value: string;
  field?: string;
  row?: number;
  confidence?: number;
  start_pos?: number;
  end_pos?: number;
  reason?: string;
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
  timestamp: string;
  version: string;
  llm?: {
    status: 'online' | 'offline';
    model: string | null;
    provider: string;
  };
  engine_available?: boolean;
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
  }));
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await apiClient.delete(`/files/${fileId}`);
};

export const downloadResult = async (
  fileId: string,
  fileType: 'result' | 'report' = 'result'
): Promise<Blob> => {
  const response = await apiClient.get(`/download/${fileId}`, {
    params: { file_type: fileType },
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
  uploadRegulation,
  updateRegulation,
  healthCheck,
};

export default api;
