/**
 * Report Entity - 報告實體
 *
 * 代表一個去識別化處理報告
 */

export interface Report {
  readonly id: string;
  readonly filename: string;
  readonly taskId: string;
  readonly jobName?: string;
  readonly filesProcessed: number;
  readonly totalPhiFound: number;
  readonly createdAt: Date;
  readonly generatedAt?: Date;
}

export interface ReportSummary {
  readonly totalRecords?: number;
  readonly phiFound?: number;
  readonly phiMasked?: number;
  readonly processingTime?: number;
  readonly filesProcessed?: number;
}

export interface ReportFileDetail {
  readonly fileId: string;
  readonly filename: string;
  readonly phiFound: number;
  readonly rowsProcessed?: number;
  readonly status: string;
}

export interface ReportDetail {
  readonly id: string;
  readonly filename: string;
  readonly sourceFileId: string;
  readonly createdAt: Date;
  readonly taskId?: string;
  readonly jobName?: string;
  readonly summary?: ReportSummary;
  readonly phiTypes?: Record<string, number>;
  readonly details?: Array<{
    field: string;
    original: string;
    masked: string;
    phiType: string;
  }>;
  readonly fileDetails?: ReportFileDetail[];
  readonly generatedAt?: Date;
}

/**
 * 從 API 響應創建 Report 實體
 */
export function createReport(data: {
  id: string;
  filename: string;
  task_id: string;
  job_name?: string;
  files_processed: number;
  total_phi_found: number;
  created_at: string;
  generated_at?: string;
}): Report {
  return {
    id: data.id,
    filename: data.filename,
    taskId: data.task_id,
    jobName: data.job_name,
    filesProcessed: data.files_processed,
    totalPhiFound: data.total_phi_found,
    createdAt: new Date(data.created_at),
    generatedAt: data.generated_at ? new Date(data.generated_at) : undefined,
  };
}

/**
 * 從 API 響應創建 ReportDetail 實體
 */
export function createReportDetail(data: {
  id: string;
  filename: string;
  source_file_id: string;
  created_at: string;
  task_id?: string;
  job_name?: string;
  summary?: {
    total_records?: number;
    phi_found?: number;
    phi_masked?: number;
    processing_time?: number;
    files_processed?: number;
  };
  phi_types?: Record<string, number>;
  details?: Array<{
    field: string;
    original: string;
    masked: string;
    phi_type: string;
  }>;
  file_details?: Array<{
    file_id: string;
    filename: string;
    phi_found: number;
    rows_processed?: number;
    status: string;
  }>;
  generated_at?: string;
}): ReportDetail {
  return {
    id: data.id,
    filename: data.filename,
    sourceFileId: data.source_file_id,
    createdAt: new Date(data.created_at),
    taskId: data.task_id,
    jobName: data.job_name,
    summary: data.summary
      ? {
          totalRecords: data.summary.total_records,
          phiFound: data.summary.phi_found,
          phiMasked: data.summary.phi_masked,
          processingTime: data.summary.processing_time,
          filesProcessed: data.summary.files_processed,
        }
      : undefined,
    phiTypes: data.phi_types,
    details: data.details?.map((d) => ({
      field: d.field,
      original: d.original,
      masked: d.masked,
      phiType: d.phi_type,
    })),
    fileDetails: data.file_details?.map((f) => ({
      fileId: f.file_id,
      filename: f.filename,
      phiFound: f.phi_found,
      rowsProcessed: f.rows_processed,
      status: f.status,
    })),
    generatedAt: data.generated_at ? new Date(data.generated_at) : undefined,
  };
}
