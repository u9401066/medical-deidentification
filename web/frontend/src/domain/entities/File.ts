/**
 * File Entity - 檔案實體
 *
 * 代表一個上傳的檔案
 */

export type FileStatusType = 'pending' | 'processing' | 'completed' | 'error';

export interface UploadedFile {
  readonly id: string;
  readonly filename: string;
  readonly size: number;
  readonly uploadTime: Date;
  readonly fileType: string;
  readonly previewAvailable: boolean;
  readonly status: FileStatusType;
}

/**
 * 從 API 響應創建 File 實體
 */
export function createUploadedFile(data: {
  id?: string;
  file_id?: string;
  filename: string;
  size: number;
  upload_time: string;
  file_type: string;
  preview_available: boolean;
  status?: string;
}): UploadedFile {
  return {
    id: data.file_id || data.id || '',
    filename: data.filename,
    size: data.size,
    uploadTime: new Date(data.upload_time),
    fileType: data.file_type,
    previewAvailable: data.preview_available,
    status: (data.status as FileStatusType) || 'pending',
  };
}

/**
 * 格式化檔案大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 取得檔案副檔名
 */
export function getFileExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === filename.length - 1) {
    return '';
  }
  return filename.slice(lastDotIndex + 1).toLowerCase();
}

/**
 * 檢查是否為支援的檔案類型
 */
export function isSupportedFileType(filename: string): boolean {
  const supportedExtensions = ['xlsx', 'xls', 'csv', 'json', 'txt'];
  return supportedExtensions.includes(getFileExtension(filename));
}
