/**
 * Shared Constants - 共享常數定義
 */

/**
 * API 端點
 */
export const API_ENDPOINTS = {
  FILES: '/files',
  TASKS: '/tasks',
  REPORTS: '/reports',
  SETTINGS: '/settings',
  HEALTH: '/health',
} as const;

/**
 * Query Keys
 */
export const QUERY_KEYS = {
  FILES: ['files'] as const,
  TASKS: ['tasks'] as const,
  REPORTS: ['reports'] as const,
  SETTINGS: ['settings'] as const,
} as const;

/**
 * 輪詢間隔 (毫秒)
 */
export const POLLING_INTERVALS = {
  TASKS: 2000,
  FILES: 5000,
} as const;

/**
 * 檔案類型
 */
export const SUPPORTED_FILE_TYPES = {
  EXCEL: ['xlsx', 'xls'],
  CSV: ['csv'],
  JSON: ['json'],
  TEXT: ['txt'],
} as const;

export const ALL_SUPPORTED_EXTENSIONS = [
  ...SUPPORTED_FILE_TYPES.EXCEL,
  ...SUPPORTED_FILE_TYPES.CSV,
  ...SUPPORTED_FILE_TYPES.JSON,
  ...SUPPORTED_FILE_TYPES.TEXT,
];
