/**
 * useDownload Hook - 下載管理 Hook
 */
import { useMutation } from '@tanstack/react-query';
import { downloadResult, downloadSingleFileResult } from '@/infrastructure/api';

export function useDownloadResult() {
  return useMutation({
    mutationFn: async ({
      taskId,
      fileType = 'result',
      format = 'xlsx',
    }: {
      taskId: string;
      fileType?: 'result' | 'report';
      format?: 'xlsx' | 'csv' | 'json';
    }) => downloadResult(taskId, fileType, format),
  });
}

export function useDownloadSingleFile() {
  return useMutation({
    mutationFn: async ({
      taskId,
      fileId,
      format = 'xlsx',
    }: {
      taskId: string;
      fileId: string;
      format?: 'xlsx' | 'csv' | 'json';
    }) => downloadSingleFileResult(taskId, fileId, format),
  });
}
