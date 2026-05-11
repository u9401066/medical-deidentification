/**
 * 共用工具函數 - 向後兼容 @/lib/utils 路徑
 *
 * 這個模組提供基礎的工具函數供 UI 元件使用
 * 遷移到 DDD 架構後，建議使用 @/shared/utils 替代
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合併 Tailwind CSS 類別
 * @param inputs - CSS 類別值
 * @returns 合併後的類別字串
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * 格式化位元組大小
 * @param bytes - 位元組數
 * @param decimals - 小數位數
 * @returns 格式化後的字串
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * 格式化日期
 * @param date - 日期字串或 Date 物件
 * @param options - 格式化選項
 * @returns 格式化後的日期字串
 */
export function formatDate(
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }
): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('zh-TW', options);
}

/**
 * 觸發瀏覽器下載並確保 object URL 被釋放。
 */
export function saveBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export function deidentifiedFilename(filename: string | undefined, fallback = 'result'): string {
  const source = filename?.trim() || fallback;
  const dotIndex = source.lastIndexOf('.');
  const rawBase = dotIndex > 0 ? source.slice(0, dotIndex) : source;
  const rawExt = dotIndex > 0 ? source.slice(dotIndex + 1).toLowerCase() : 'txt';
  const extension = rawExt === 'xls' ? 'xlsx' : rawExt || 'txt';
  const base = rawBase || fallback;
  return `${base}_deidentified.${extension}`;
}

export function deidentifiedDownloadFilename(
  taskId: string,
  filenames: Array<string | undefined> | undefined
): string {
  const validNames = (filenames || []).filter(Boolean) as string[];
  if (validNames.length === 1) {
    return deidentifiedFilename(validNames[0], taskId);
  }
  return `result_${taskId}_deidentified.zip`;
}
