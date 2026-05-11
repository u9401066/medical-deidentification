/**
 * useResults Hook - 結果管理 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { getResults, getResultDetail } from '@/infrastructure/api';
import type { ResultItem, ResultDetail } from '@/infrastructure/api';

export const RESULTS_QUERY_KEY = ['results'] as const;
export const RESULT_DETAIL_QUERY_KEY = (taskId: string, revealPhi = false) =>
  ['results', taskId, { revealPhi }] as const;

export function useResults() {
  const query = useQuery({
    queryKey: RESULTS_QUERY_KEY,
    queryFn: getResults,
  });

  return {
    results: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}

export function useResultDetail(taskId: string | null, revealPhi = false) {
  return useQuery<ResultDetail>({
    queryKey: RESULT_DETAIL_QUERY_KEY(taskId ?? '', revealPhi),
    queryFn: () => getResultDetail(taskId!, revealPhi),
    enabled: !!taskId,
  });
}

export { type ResultItem, type ResultDetail };
