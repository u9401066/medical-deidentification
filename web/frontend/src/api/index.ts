import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  // 計時相關
  started_at?: string;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
  processing_speed?: number;  // chars per second
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

// ============================================================
// File APIs
// ============================================================

export const uploadFile = async (file: File): Promise<UploadedFile> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listFiles = async (): Promise<UploadedFile[]> => {
  const response = await api.get('/files');
  // 後端返回 file_id，前端使用 id
  return response.data.map((f: any) => ({
    ...f,
    id: f.file_id || f.id,
    status: f.status || 'pending',
  }));
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await api.delete(`/files/${fileId}`);
};

export const downloadResult = async (fileId: string, fileType: 'result' | 'report' = 'result'): Promise<Blob> => {
  const response = await api.get(`/download/${fileId}`, {
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
  const response = await api.get(`/preview/${fileId}`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

// ============================================================
// Processing APIs
// ============================================================

export const startProcessing = async (request: ProcessRequest): Promise<TaskStatus> => {
  const response = await api.post('/process', request);
  return response.data;
};

export const listTasks = async (): Promise<TaskStatus[]> => {
  const response = await api.get('/tasks');
  return response.data;
};

export const getTask = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data;
};

// ============================================================
// Results & Reports APIs
// ============================================================

export interface ResultItem {
  task_id: string
  filename: string
  phi_count: number
  status: string
  created_at: string
  results?: Array<{
    file_id: string
    filename: string
    phi_found: number
    rows_processed?: number
    status: string
  }>
}

export interface PHIEntity {
  type: string
  value: string
  masked_value: string
  field?: string
  row?: number
  confidence?: number
  start_pos?: number
  end_pos?: number
  reason?: string
}

export interface ResultDetail {
  task_id: string
  job_name: string
  config: {
    masking_type: string
    phi_types: string[]
  }
  results: Array<{
    file_id: string
    filename: string
    phi_found: number
    phi_by_type?: Record<string, number>
    rows_processed?: number
    status: string
    phi_entities?: PHIEntity[]
    original_data?: Record<string, unknown>[]
    masked_data?: Record<string, unknown>[]
    original_content?: string
    masked_content?: string
    output_path?: string
  }>
  processed_at: string
}

export const getResults = async (): Promise<ResultItem[]> => {
  const response = await api.get(`/results`);
  return response.data;
};

export const getReport = async (taskId: string): Promise<ReportDetail> => {
  const response = await api.get(`/reports/${taskId}`);
  return response.data;
};

export const getResultDetail = async (taskId: string): Promise<ResultDetail> => {
  const response = await api.get(`/results/${taskId}`);
  return response.data;
};

export const listReports = async (): Promise<Report[]> => {
  const response = await api.get('/reports');
  return response.data;
};

// ============================================================
// Settings APIs
// ============================================================

export const getPHITypes = async (): Promise<PHIType[]> => {
  const response = await api.get('/settings/phi-types');
  return response.data.phi_types || response.data;
};

export const getConfig = async (): Promise<PHIConfig> => {
  const response = await api.get('/settings/config');
  return response.data;
};

export const updateConfig = async (config: PHIConfig): Promise<{ message: string; config: PHIConfig }> => {
  const response = await api.put('/settings/config', config);
  return response.data;
};

// ============================================================
// Regulations APIs
// ============================================================

export const listRegulations = async (): Promise<RegulationRule[]> => {
  const response = await api.get('/regulations');
  return response.data;
};

export const uploadRegulation = async (file: File): Promise<{ message: string; rules: RegulationRule[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/regulations/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateRegulation = async (
  ruleId: string,
  enabled: boolean
): Promise<{ message: string; rule_id: string; enabled: boolean }> => {
  const response = await api.put(`/regulations/${ruleId}`, null, {
    params: { enabled },
  });
  return response.data;
};

// ============================================================
// Health Check
// ============================================================

export interface HealthStatus {
  status: string
  timestamp: string
  version: string
  llm?: {
    status: 'online' | 'offline'
    model: string | null
    provider: string
  }
  engine_available?: boolean
}

export const healthCheck = async (): Promise<HealthStatus> => {
  const response = await api.get('/health');
  return response.data;
};

// ============================================================
// Export all as a single object for convenience
// ============================================================

export default {
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
