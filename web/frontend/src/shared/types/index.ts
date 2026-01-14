/**
 * Shared Types - 共享類型定義
 *
 * 策略：從 @/infrastructure/api 統一導出類型，確保與現有程式碼兼容
 * DDD 層的 domain/entities 提供增強功能（factory functions）
 */

// ============================================================
// 從 Infrastructure API 層 Re-export 類型（主要來源，保持兼容性）
// ============================================================
export type {
  UploadedFile,
  PHIConfig,
  TaskStatus,
  ProcessRequest,
  PreviewData,
  PHIType,
  MaskingType,
  RegulationRule,
  Report,
  ResultItem,
  ResultDetail,
  PHIEntity,
  HealthStatus,
} from '@/infrastructure/api';

// ============================================================
// 從 Domain 層 Re-export 增強功能
// ============================================================
export {
  // Task entity helpers
  createTask,
  isTaskCompleted,
  isTaskProcessing,
  isTaskFailed,
  formatTaskTime,
} from '@/domain/entities/Task';

export {
  // File entity helpers
  createUploadedFile,
  formatFileSize,
  getFileExtension,
  isSupportedFileType,
} from '@/domain/entities/File';

export {
  // Report entity helpers
  createReport,
  createReportDetail,
} from '@/domain/entities/Report';

// Domain 層的類型別名（為了清晰區分）
export type { Task } from '@/domain/entities/Task';
export type { FileStatusType } from '@/domain/entities/File';
export type { ReportDetail, ReportSummary } from '@/domain/entities/Report';
