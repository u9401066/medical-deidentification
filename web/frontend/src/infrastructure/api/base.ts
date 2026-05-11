import type { AxiosResponse } from 'axios';

export function resolveApiBase(): string {
  const configured =
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_BASE;

  if (configured) {
    return configured;
  }

  return '/api';
}

export const API_BASE = resolveApiBase();

export function ensureApiResponse<T>(response: AxiosResponse<T>): AxiosResponse<T> {
  const contentType = String(response.headers?.['content-type'] || '');

  if (contentType.includes('text/html')) {
    throw new Error(
      `API endpoint returned HTML instead of JSON. Check API base URL: ${API_BASE}`
    );
  }

  return response;
}
