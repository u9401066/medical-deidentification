/**
 * useHealth Hook - 健康檢查 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { healthCheck } from '@/infrastructure/api';
import type { HealthStatus } from '@/infrastructure/api';

export const HEALTH_QUERY_KEY = ['health'] as const;

export function useHealth(options?: { refetchInterval?: number }) {
  const query = useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: healthCheck,
    refetchInterval: options?.refetchInterval ?? 30000,
  });

  return {
    health: query.data ?? null,
    isOnline: query.data?.llm?.status === 'online',
    llmModel: query.data?.llm?.model ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

export { type HealthStatus };
