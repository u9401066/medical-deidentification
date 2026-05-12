/**
 * API Client - HTTP 客戶端配置
 */
import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import { logger } from '../logging';
import { API_BASE, ensureApiResponse } from './base';

function isFormDataBody(value: unknown): value is FormData {
  return typeof FormData !== 'undefined' && value instanceof FormData;
}

/**
 * 創建 Axios 實例
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 秒超時
});

// 請求攔截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (isFormDataBody(config.data)) {
      config.headers.delete?.('Content-Type');
      delete config.headers['Content-Type'];
      delete config.headers['content-type'];
    }
    logger.debug('API Request', {
      method: config.method?.toUpperCase(),
      url: config.url,
      params: config.params,
    });
    return config;
  },
  (error: AxiosError) => {
    logger.error('API Request Error', { error: error.message });
    return Promise.reject(error);
  }
);

// 響應攔截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    ensureApiResponse(response);
    logger.debug('API Response', {
      status: response.status,
      url: response.config.url,
    });
    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    if (typeof window !== 'undefined' && status !== undefined && [401, 403].includes(status)) {
      window.dispatchEvent(
        new CustomEvent('medical-deid-auth-error', {
          detail: { status },
        })
      );
    }
    const errorInfo = {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
    };
    logger.error('API Response Error', errorInfo);
    return Promise.reject(error);
  }
);

export default apiClient;
