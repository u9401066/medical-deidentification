/**
 * useFiles Hook - 檔案管理 Hook
 *
 * 提供檔案上傳、列表、刪除等功能
 */
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { logger } from '@/infrastructure/logging';
import {
  listFiles,
  uploadFile,
  deleteFile,
  previewFile,
  PreviewData,
} from '@/infrastructure/api/files';
import { UploadedFile } from '@/domain/entities/File';

// Query Keys
export const FILES_QUERY_KEY = ['files'] as const;
export const FILE_PREVIEW_QUERY_KEY = (fileId: string) =>
  ['files', fileId, 'preview'] as const;

/**
 * 取得檔案列表
 */
export function useFiles() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: FILES_QUERY_KEY,
    queryFn: async () => {
      logger.debug('Fetching files');
      return listFiles();
    },
  });

  // 刷新檔案列表
  const refresh = () => {
    logger.info('Refreshing files');
    queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
  };

  return {
    files: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refresh,
  };
}

/**
 * 上傳檔案 Mutation
 */
export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      logger.info('Uploading file', { filename: file.name, size: file.size });
      return uploadFile(file);
    },
    onSuccess: (uploadedFile) => {
      logger.info('File uploaded', {
        fileId: uploadedFile.id,
        filename: uploadedFile.filename,
      });
      // 刷新檔案列表
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
    },
    onError: (error) => {
      logger.error('File upload failed', { error: String(error) });
    },
  });
}

/**
 * 刪除檔案 Mutation
 */
export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fileId: string) => {
      logger.info('Deleting file', { fileId });
      return deleteFile(fileId);
    },
    onSuccess: (_, fileId) => {
      logger.info('File deleted', { fileId });
      // 刷新檔案列表
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
    },
    onError: (error) => {
      logger.error('File delete failed', { error: String(error) });
    },
  });
}

/**
 * 取得檔案預覽
 */
export function useFilePreview(
  fileId: string | null,
  options?: { page?: number; pageSize?: number }
) {
  return useQuery({
    queryKey: FILE_PREVIEW_QUERY_KEY(fileId ?? ''),
    queryFn: async (): Promise<PreviewData> => {
      if (!fileId) throw new Error('File ID is required');
      logger.debug('Fetching file preview', { fileId, ...options });
      return previewFile(fileId, options?.page ?? 1, options?.pageSize ?? 20);
    },
    enabled: !!fileId,
  });
}

export default {
  useFiles,
  useUploadFile,
  useDeleteFile,
  useFilePreview,
};
