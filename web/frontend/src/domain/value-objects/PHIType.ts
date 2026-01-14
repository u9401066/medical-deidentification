/**
 * PHIType Value Object - PHI 類型值物件
 */

export interface PHIType {
  readonly type: string;
  readonly displayName: string;
  readonly description: string;
  readonly category: string;
  readonly defaultMasking?: string;
}

/**
 * 從 API 響應創建 PHIType
 */
export function createPHIType(data: {
  type: string;
  display_name: string;
  description: string;
  category: string;
  default_masking?: string;
}): PHIType {
  return {
    type: data.type,
    displayName: data.display_name,
    description: data.description,
    category: data.category,
    defaultMasking: data.default_masking,
  };
}

/**
 * PHI 類型分類
 */
export const PHI_CATEGORIES = {
  IDENTIFIER: '識別碼',
  DEMOGRAPHIC: '人口統計',
  MEDICAL: '醫療資訊',
  CONTACT: '聯絡資訊',
  FINANCIAL: '財務資訊',
  OTHER: '其他',
} as const;

export type PHICategory = keyof typeof PHI_CATEGORIES;

/**
 * 依類別分組 PHI 類型
 */
export function groupPHITypesByCategory(
  phiTypes: PHIType[]
): Record<string, PHIType[]> {
  return phiTypes.reduce(
    (groups, phiType) => {
      const category = phiType.category || 'OTHER';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(phiType);
      return groups;
    },
    {} as Record<string, PHIType[]>
  );
}
