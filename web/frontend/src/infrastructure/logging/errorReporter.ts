/**
 * Error Reporter - 前端錯誤回報到後端
 */
import { apiClient } from '../api/client';

interface ErrorReport {
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  timestamp: string;
  type: 'js-error' | 'react-error' | 'api-error' | 'unhandled-rejection';
  extra?: Record<string, unknown>;
}

const errorQueue: ErrorReport[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * 發送錯誤報告到後端
 */
async function flushErrors() {
  if (errorQueue.length === 0) return;
  
  const errors = [...errorQueue];
  errorQueue.length = 0;
  
  try {
    await apiClient.post('/logs/frontend-errors', { errors });
  } catch {
    // 如果發送失敗，輸出到 console
    console.error('[ErrorReporter] Failed to send errors to backend:', errors);
  }
}

/**
 * 排程發送（debounce）
 */
function scheduleFlush() {
  if (flushTimer) clearTimeout(flushTimer);
  flushTimer = setTimeout(flushErrors, 1000);
}

/**
 * 報告錯誤
 */
export function reportError(
  error: Error | string,
  type: ErrorReport['type'] = 'js-error',
  extra?: Record<string, unknown>
) {
  const report: ErrorReport = {
    message: typeof error === 'string' ? error : error.message,
    stack: typeof error === 'string' ? undefined : error.stack,
    url: window.location.href,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    type,
    extra,
  };
  
  errorQueue.push(report);
  scheduleFlush();
  
  // 同時輸出到 console 方便開發
  console.error(`[${type}]`, report.message, extra || '');
}

/**
 * 設定全域錯誤處理
 */
export function setupGlobalErrorHandlers() {
  // JavaScript 錯誤
  window.onerror = (message, source, lineno, colno, error) => {
    reportError(error || String(message), 'js-error', {
      source,
      lineno,
      colno,
    });
    return false;
  };

  // Promise rejection
  window.onunhandledrejection = (event) => {
    const error = event.reason;
    reportError(
      error instanceof Error ? error : String(error),
      'unhandled-rejection'
    );
  };

  console.log('[ErrorReporter] Global error handlers installed');
}

/**
 * React Error Boundary 用
 */
export function reportReactError(error: Error, componentStack: string) {
  const report: ErrorReport = {
    message: error.message,
    stack: error.stack,
    componentStack,
    url: window.location.href,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    type: 'react-error',
  };
  
  errorQueue.push(report);
  scheduleFlush();
  
  console.error('[react-error]', error.message, { componentStack });
}
