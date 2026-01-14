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

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * 創建 Axios 實例
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 秒超時
});

// 請求攔截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
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
    logger.debug('API Response', {
      status: response.status,
      url: response.config.url,
    });
    return response;
  },
  (error: AxiosError) => {
    const errorInfo = {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
      data: error.response?.data,
    };
    logger.error('API Response Error', errorInfo);
    return Promise.reject(error);
  }
);

export default apiClient;
