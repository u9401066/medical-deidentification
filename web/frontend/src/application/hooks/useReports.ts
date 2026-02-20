/**
 * useReports Hook - 報告管理 Hook
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  listReports,
  getReport,
  exportReport,
} from '@/infrastructure/api';
import type { Report, ReportDetail, ReportExportFormat } from '@/infrastructure/api';

export const REPORTS_QUERY_KEY = ['reports'] as const;
export const REPORT_DETAIL_QUERY_KEY = (taskId: string) =>
  ['reports', taskId] as const;

export function useReports() {
  const query = useQuery({
    queryKey: REPORTS_QUERY_KEY,
    queryFn: listReports,
  });

  return {
    reports: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

export function useReportDetail(taskId: string | null) {
  return useQuery<ReportDetail>({
    queryKey: REPORT_DETAIL_QUERY_KEY(taskId ?? ''),
    queryFn: () => getReport(taskId!),
    enabled: !!taskId,
  });
}

export function useExportReport() {
  return useMutation({
    mutationFn: async ({
      taskId,
      format,
    }: {
      taskId: string;
      format: ReportExportFormat;
    }) => exportReport(taskId, format),
  });
}

export { type Report, type ReportDetail, type ReportExportFormat };
