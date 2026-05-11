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
      revealPhi = false,
    }: {
      taskId: string;
      fileType?: 'result' | 'report';
      format?: 'xlsx' | 'csv' | 'json';
      revealPhi?: boolean;
    }) => downloadResult(taskId, fileType, format, revealPhi),
  });
}

export function useDownloadSingleFile() {
  return useMutation({
    mutationFn: async ({
      taskId,
      fileId,
      format = 'xlsx',
      revealPhi = false,
    }: {
      taskId: string;
      fileId: string;
      format?: 'xlsx' | 'csv' | 'json';
      revealPhi?: boolean;
    }) => downloadSingleFileResult(taskId, fileId, format, revealPhi),
  });
}
