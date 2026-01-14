/**
 * Logger - 日誌系統
 *
 * 支援終端輸出，Agent 可讀取
 */

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
}

// 全域日誌存儲（開發模式）
declare global {
  interface Window {
    __FRONTEND_LOGS__?: LogEntry[];
  }
}

const LOG_COLORS: Record<LogLevel, string> = {
  DEBUG: '\x1b[36m', // cyan
  INFO: '\x1b[32m', // green
  WARN: '\x1b[33m', // yellow
  ERROR: '\x1b[31m', // red
};

const RESET_COLOR = '\x1b[0m';

function log(level: LogLevel, message: string, context?: object): void {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    context: context as Record<string, unknown>,
  };

  // 開發模式：輸出到 console 並存儲到全域變數
  if (import.meta.env.DEV) {
    const color = LOG_COLORS[level];
    const prefix = `${color}[${level}]${RESET_COLOR}`;

    if (context) {
      console.log(prefix, message, context);
    } else {
      console.log(prefix, message);
    }

    // 存儲到全域變數供 Agent 查詢
    if (typeof window !== 'undefined') {
      window.__FRONTEND_LOGS__ = window.__FRONTEND_LOGS__ ?? [];
      window.__FRONTEND_LOGS__.push(entry);

      // 限制日誌數量（最多保留 1000 條）
      if (window.__FRONTEND_LOGS__.length > 1000) {
        window.__FRONTEND_LOGS__ = window.__FRONTEND_LOGS__.slice(-500);
      }
    }
  }

  // 生產模式：錯誤和警告仍然輸出
  if (!import.meta.env.DEV && (level === 'ERROR' || level === 'WARN')) {
    console.log(`[${level}]`, message, context ?? '');
  }
}

/**
 * Logger 實例
 *
 * 使用方式：
 * ```typescript
 * import { logger } from '@/infrastructure/logging';
 *
 * logger.info('Task started', { taskId: '123' });
 * logger.error('API failed', { error: err.message });
 * ```
 *
 * Agent 讀取日誌（在瀏覽器 DevTools Console）：
 * ```javascript
 * window.__FRONTEND_LOGS__
 * window.__FRONTEND_LOGS__.filter(l => l.level === 'ERROR')
 * ```
 */
export const logger = {
  debug: (message: string, context?: object) => log('DEBUG', message, context),
  info: (message: string, context?: object) => log('INFO', message, context),
  warn: (message: string, context?: object) => log('WARN', message, context),
  error: (message: string, context?: object) => log('ERROR', message, context),
};

/**
 * 取得所有日誌（供 Agent 使用）
 */
export function getAllLogs(): LogEntry[] {
  if (typeof window !== 'undefined' && window.__FRONTEND_LOGS__) {
    return [...window.__FRONTEND_LOGS__];
  }
  return [];
}

/**
 * 依級別篩選日誌
 */
export function getLogsByLevel(level: LogLevel): LogEntry[] {
  return getAllLogs().filter((log) => log.level === level);
}

/**
 * 清除所有日誌
 */
export function clearLogs(): void {
  if (typeof window !== 'undefined') {
    window.__FRONTEND_LOGS__ = [];
  }
}

export default logger;
