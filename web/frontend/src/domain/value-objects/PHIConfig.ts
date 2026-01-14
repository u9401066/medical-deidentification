/**
 * PHIConfig Value Object - PHI 配置值物件
 *
 * 不可變的配置物件
 */

export type MaskingType = 'mask' | 'hash' | 'replace' | 'delete' | 'keep';

export interface PHITypeConfig {
  readonly enabled?: boolean;
  readonly masking?: MaskingType;
}

export interface PHIConfig {
  readonly enabled?: boolean;
  readonly strictMode?: boolean;
  readonly defaultMasking?: MaskingType;
  readonly maskingType?: string;
  readonly phiTypes?: Record<string, PHITypeConfig>;
  readonly preserveFormat?: boolean;
  readonly customPatterns?: Record<string, string>;
}

/**
 * 從 API 響應創建 PHIConfig
 */
export function createPHIConfig(data: {
  enabled?: boolean;
  strict_mode?: boolean;
  default_masking?: string;
  masking_type?: string;
  phi_types?: Record<string, { enabled?: boolean; masking?: string }>;
  preserve_format?: boolean;
  custom_patterns?: Record<string, string>;
}): PHIConfig {
  return {
    enabled: data.enabled,
    strictMode: data.strict_mode,
    defaultMasking: data.default_masking as MaskingType,
    maskingType: data.masking_type,
    phiTypes: data.phi_types
      ? Object.fromEntries(
          Object.entries(data.phi_types).map(([key, value]) => [
            key,
            {
              enabled: value.enabled,
              masking: value.masking as MaskingType,
            },
          ])
        )
      : undefined,
    preserveFormat: data.preserve_format,
    customPatterns: data.custom_patterns,
  };
}

/**
 * 轉換 PHIConfig 為 API 請求格式
 */
export function toPHIConfigRequest(config: PHIConfig): Record<string, unknown> {
  return {
    enabled: config.enabled,
    strict_mode: config.strictMode,
    default_masking: config.defaultMasking,
    masking_type: config.maskingType,
    phi_types: config.phiTypes
      ? Object.fromEntries(
          Object.entries(config.phiTypes).map(([key, value]) => [
            key,
            {
              enabled: value.enabled,
              masking: value.masking,
            },
          ])
        )
      : undefined,
    preserve_format: config.preserveFormat,
    custom_patterns: config.customPatterns,
  };
}

/**
 * 創建預設 PHIConfig
 */
export function createDefaultPHIConfig(): PHIConfig {
  return {
    enabled: true,
    strictMode: false,
    defaultMasking: 'mask',
    preserveFormat: true,
  };
}
