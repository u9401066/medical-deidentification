/**
 * PHI Config Schema - 去識別化設定驗證
 *
 * 使用 Zod 進行表單驗證
 */
import { z } from 'zod';

/**
 * 遮蔽類型
 */
export const maskingTypeSchema = z.enum(['redact', 'replace', 'tag']);

export type MaskingType = z.infer<typeof maskingTypeSchema>;

/**
 * PHI 類型
 */
export const phiTypeSchema = z.enum([
  'PERSON',
  'ID',
  'PHONE',
  'ADDRESS',
  'DATE',
  'MEDICAL_RECORD',
  'ORGANIZATION',
  'EMAIL',
  'URL',
  'FINANCIAL',
]);

export type PHIType = z.infer<typeof phiTypeSchema>;

/**
 * 進階選項 Schema
 */
export const advancedOptionsSchema = z.object({
  // 使用 RAG 增強
  useRAG: z.boolean().default(false),
  // 批次大小
  batchSize: z.number().min(1).max(100).default(10),
  // 平行處理數
  parallelism: z.number().min(1).max(8).default(4),
});

/**
 * 任務設定 Schema
 */
export const taskConfigSchema = z.object({
  // 檔案
  files: z
    .array(z.string())
    .min(1, '請選擇至少一個檔案'),

  // 遮蔽類型
  maskingType: maskingTypeSchema.default('redact'),

  // PHI 類型選擇
  phiTypes: z
    .array(phiTypeSchema)
    .min(1, '請選擇至少一種 PHI 類型')
    .default(['PERSON', 'ID', 'PHONE', 'ADDRESS', 'DATE']),

  // 信心度閾值
  confidence: z
    .number()
    .min(0.5, '信心度至少 0.5')
    .max(1.0, '信心度最高 1.0')
    .default(0.85),

  // 自訂替換文字 (僅 replace 模式)
  customReplacement: z.string().optional(),

  // 保留原始格式
  preserveFormat: z.boolean().default(true),

  // 進階選項
  advanced: advancedOptionsSchema.optional(),
}).refine(
  (data) => {
    // 如果選擇 replace，必須提供自訂替換文字
    if (data.maskingType === 'replace') {
      return data.customReplacement && data.customReplacement.length > 0;
    }
    return true;
  },
  {
    message: '使用替換模式時必須提供替換文字',
    path: ['customReplacement'],
  }
);

export type TaskConfig = z.infer<typeof taskConfigSchema>;

/**
 * 預設設定
 */
export const defaultTaskConfig = {
  files: [] as string[],
  maskingType: 'redact' as MaskingType,
  phiTypes: ['PERSON', 'ID', 'PHONE', 'ADDRESS', 'DATE'] as PHIType[],
  confidence: 0.85,
  preserveFormat: true,
  advanced: {
    useRAG: false,
    batchSize: 10,
    parallelism: 4,
  },
};
