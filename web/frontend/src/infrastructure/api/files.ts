/**
 * Files API - 檔案相關 API
 */
import { apiClient } from './client';
import { logger } from '../logging';
import { UploadedFile, createUploadedFile } from '@/domain/entities/File';

// API 響應類型
interface FileResponse {
  id?: string;
  file_id?: string;
  filename: string;
  size: number;
  upload_time: string;
  file_type: string;
  preview_available: boolean;
  status?: string;
}

export interface PreviewData {
  type: 'tabular' | 'text' | 'json';
  columns?: string[];
  data?: Record<string, unknown>[];
  content?: string;
  lines?: string[];
  totalRows: number;
  totalLines?: number;
  totalItems?: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

/**
 * 上傳檔案
 */
export async function uploadFile(file: File): Promise<UploadedFile> {
  logger.info('Uploading file', { filename: file.name, size: file.size });

  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<FileResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  const uploadedFile = createUploadedFile(response.data);
  logger.info('File uploaded successfully', {
    fileId: uploadedFile.id,
    filename: uploadedFile.filename,
  });
  return uploadedFile;
}

/**
 * 取得檔案列表
 */
export async function listFiles(): Promise<UploadedFile[]> {
  logger.debug('Fetching file list');
  const response = await apiClient.get<FileResponse[]>('/files');
  return response.data.map((f: FileResponse) =>
    createUploadedFile({
      ...f,
      id: f.file_id || f.id,
      status: f.status || 'pending',
    })
  );
}

/**
 * 刪除檔案
 */
export async function deleteFile(fileId: string): Promise<void> {
  logger.info('Deleting file', { fileId });
  await apiClient.delete(`/files/${fileId}`);
  logger.info('File deleted successfully', { fileId });
}

/**
 * 下載結果
 */
export async function downloadResult(
  fileId: string,
  fileType: 'result' | 'report' = 'result'
): Promise<Blob> {
  logger.info('Downloading result', { fileId, fileType });
  const response = await apiClient.get(`/download/${fileId}`, {
    params: { file_type: fileType },
    responseType: 'blob',
  });
  return response.data;
}

/**
 * 預覽檔案
 */
export async function previewFile(
  fileId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PreviewData> {
  logger.debug('Fetching file preview', { fileId, page, pageSize });
  const response = await apiClient.get(`/preview/${fileId}`, {
    params: { page, page_size: pageSize },
  });

  const data = response.data;
  return {
    type: data.type,
    columns: data.columns,
    data: data.data,
    content: data.content,
    lines: data.lines,
    totalRows: data.total_rows,
    totalLines: data.total_lines,
    totalItems: data.total_items,
    page: data.page,
    pageSize: data.page_size,
    hasMore: data.has_more,
  };
}

export default {
  uploadFile,
  listFiles,
  deleteFile,
  downloadResult,
  previewFile,
};
