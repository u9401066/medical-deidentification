```skill
---
name: react-form
description: React Hook Form + Zod 表單驗證最佳實踐。Triggers: form, 表單, validation, 驗證, zod, react-hook-form.
---

# React Form 表單驗證技能

## 描述

使用 React Hook Form + Zod 實現類型安全的表單驗證。

## 觸發條件

- 「form」「表單」
- 「validation」「驗證」
- 「zod」「react-hook-form」

## 參照規範

- 子法：`.github/bylaws/frontend-ddd.md`

---

## 為什麼選擇這個組合？

| 特點 | React Hook Form | Formik | 原生 |
|------|-----------------|--------|------|
| Re-render | 極少 (uncontrolled) | 多 | 多 |
| Bundle | ~9KB | ~13KB | 0 |
| 型別推導 | ✅ (with Zod) | 部分 | 手動 |
| 驗證整合 | 完美 | 良好 | 手動 |

---

## 基本使用

### 定義 Schema (Zod)

```typescript
// domain/value-objects/schemas/taskConfigSchema.ts
import { z } from 'zod';

export const taskConfigSchema = z.object({
  // 基本欄位
  taskName: z
    .string()
    .min(1, '任務名稱為必填')
    .max(100, '任務名稱不可超過 100 字'),

  // 枚舉選項
  maskingType: z.enum(['redact', 'replace', 'tag'], {
    errorMap: () => ({ message: '請選擇遮蔽類型' }),
  }),

  // 可選欄位
  description: z.string().optional(),

  // 數字 + 範圍
  confidence: z
    .number()
    .min(0.5, '信心度至少 0.5')
    .max(1.0, '信心度最高 1.0'),

  // 布林值
  preserveFormat: z.boolean().default(true),

  // 陣列
  phiTypes: z
    .array(z.string())
    .min(1, '至少選擇一種 PHI 類型'),

  // 條件驗證
  customReplacement: z.string().optional(),
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

// 自動推導 TypeScript 類型
export type TaskConfig = z.infer<typeof taskConfigSchema>;
```

### 建立表單元件

```typescript
// presentation/components/TaskConfigForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { taskConfigSchema, TaskConfig } from '@/domain/value-objects/schemas/taskConfigSchema';

interface TaskConfigFormProps {
  onSubmit: (data: TaskConfig) => void;
  defaultValues?: Partial<TaskConfig>;
}

export function TaskConfigForm({ onSubmit, defaultValues }: TaskConfigFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting, isDirty },
    reset,
  } = useForm<TaskConfig>({
    resolver: zodResolver(taskConfigSchema),
    defaultValues: {
      taskName: '',
      maskingType: 'redact',
      confidence: 0.85,
      preserveFormat: true,
      phiTypes: [],
      ...defaultValues,
    },
  });

  // 監聽欄位變化
  const maskingType = watch('maskingType');

  const handleFormSubmit = async (data: TaskConfig) => {
    await onSubmit(data);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      {/* 文字輸入 */}
      <div>
        <label htmlFor="taskName" className="block text-sm font-medium">
          任務名稱
        </label>
        <input
          {...register('taskName')}
          id="taskName"
          className="mt-1 block w-full rounded-md border"
        />
        {errors.taskName && (
          <p className="mt-1 text-sm text-red-600">{errors.taskName.message}</p>
        )}
      </div>

      {/* Select 選單 */}
      <div>
        <label htmlFor="maskingType" className="block text-sm font-medium">
          遮蔽類型
        </label>
        <select {...register('maskingType')} id="maskingType" className="mt-1 block w-full">
          <option value="redact">塗黑 (Redact)</option>
          <option value="replace">替換 (Replace)</option>
          <option value="tag">標記 (Tag)</option>
        </select>
        {errors.maskingType && (
          <p className="mt-1 text-sm text-red-600">{errors.maskingType.message}</p>
        )}
      </div>

      {/* 條件欄位 */}
      {maskingType === 'replace' && (
        <div>
          <label htmlFor="customReplacement" className="block text-sm font-medium">
            替換文字
          </label>
          <input
            {...register('customReplacement')}
            id="customReplacement"
            placeholder="例如：[REDACTED]"
            className="mt-1 block w-full rounded-md border"
          />
          {errors.customReplacement && (
            <p className="mt-1 text-sm text-red-600">{errors.customReplacement.message}</p>
          )}
        </div>
      )}

      {/* 數字滑桿 */}
      <div>
        <label htmlFor="confidence" className="block text-sm font-medium">
          信心度閾值: {watch('confidence')}
        </label>
        <input
          {...register('confidence', { valueAsNumber: true })}
          id="confidence"
          type="range"
          min="0.5"
          max="1.0"
          step="0.05"
          className="mt-1 block w-full"
        />
        {errors.confidence && (
          <p className="mt-1 text-sm text-red-600">{errors.confidence.message}</p>
        )}
      </div>

      {/* Checkbox */}
      <div className="flex items-center">
        <input
          {...register('preserveFormat')}
          id="preserveFormat"
          type="checkbox"
          className="h-4 w-4 rounded border"
        />
        <label htmlFor="preserveFormat" className="ml-2 text-sm">
          保留原始格式
        </label>
      </div>

      {/* 送出按鈕 */}
      <button
        type="submit"
        disabled={isSubmitting || !isDirty}
        className="rounded-md bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
      >
        {isSubmitting ? '處理中...' : '建立任務'}
      </button>
    </form>
  );
}
```

---

## 進階模式

### 陣列欄位 (useFieldArray)

```typescript
import { useForm, useFieldArray } from 'react-hook-form';

const ruleSchema = z.object({
  rules: z.array(z.object({
    pattern: z.string().min(1),
    replacement: z.string().min(1),
  })).min(1, '至少需要一條規則'),
});

type RuleForm = z.infer<typeof ruleSchema>;

function RulesForm() {
  const { control, register, handleSubmit } = useForm<RuleForm>({
    resolver: zodResolver(ruleSchema),
    defaultValues: { rules: [{ pattern: '', replacement: '' }] },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'rules',
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {fields.map((field, index) => (
        <div key={field.id} className="flex gap-2">
          <input {...register(`rules.${index}.pattern`)} placeholder="Pattern" />
          <input {...register(`rules.${index}.replacement`)} placeholder="Replacement" />
          <button type="button" onClick={() => remove(index)}>刪除</button>
        </div>
      ))}
      <button type="button" onClick={() => append({ pattern: '', replacement: '' })}>
        新增規則
      </button>
    </form>
  );
}
```

### 與 Radix UI 整合

```typescript
// 使用 Controller 整合受控元件
import { Controller } from 'react-hook-form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

function FormWithRadix() {
  const { control, handleSubmit } = useForm<TaskConfig>({
    resolver: zodResolver(taskConfigSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        control={control}
        name="maskingType"
        render={({ field }) => (
          <Select onValueChange={field.onChange} defaultValue={field.value}>
            <SelectTrigger>
              <SelectValue placeholder="選擇遮蔽類型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="redact">塗黑</SelectItem>
              <SelectItem value="replace">替換</SelectItem>
              <SelectItem value="tag">標記</SelectItem>
            </SelectContent>
          </Select>
        )}
      />
    </form>
  );
}
```

### 檔案上傳

```typescript
const fileSchema = z.object({
  file: z
    .instanceof(FileList)
    .refine((files) => files.length > 0, '請選擇檔案')
    .refine(
      (files) => files[0]?.size <= 10 * 1024 * 1024,
      '檔案大小不可超過 10MB'
    )
    .refine(
      (files) => ['application/pdf', 'text/plain'].includes(files[0]?.type),
      '只接受 PDF 或 TXT 檔案'
    ),
});

function FileUploadForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(fileSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('file')} type="file" accept=".pdf,.txt" />
      {errors.file && <p className="text-red-600">{errors.file.message}</p>}
    </form>
  );
}
```

---

## 自訂 Zod 驗證

```typescript
// domain/value-objects/schemas/customValidators.ts

// 台灣身分證字號
export const taiwanIdSchema = z.string().refine(
  (val) => {
    if (!/^[A-Z][12]\d{8}$/.test(val)) return false;
    // 驗證檢查碼...
    return true;
  },
  { message: '無效的身分證字號' }
);

// 電話號碼 (台灣)
export const phoneSchema = z.string().regex(
  /^(0[2-9]\d{7,8}|09\d{8})$/,
  '請輸入有效的電話號碼'
);

// 密碼強度
export const passwordSchema = z
  .string()
  .min(8, '密碼至少 8 個字元')
  .regex(/[A-Z]/, '需包含大寫字母')
  .regex(/[a-z]/, '需包含小寫字母')
  .regex(/[0-9]/, '需包含數字')
  .regex(/[^A-Za-z0-9]/, '需包含特殊字元');
```

---

## 測試

```typescript
// tests/unit/components/TaskConfigForm.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskConfigForm } from '@/presentation/components/TaskConfigForm';

describe('TaskConfigForm', () => {
  it('should show validation error for empty task name', async () => {
    const onSubmit = vi.fn();
    render(<TaskConfigForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole('button', { name: /建立任務/i }));

    expect(await screen.findByText(/任務名稱為必填/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('should submit valid form data', async () => {
    const onSubmit = vi.fn();
    render(<TaskConfigForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/任務名稱/i), 'Test Task');
    await userEvent.click(screen.getByRole('button', { name: /建立任務/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ taskName: 'Test Task' })
      );
    });
  });

  it('should show conditional field for replace mode', async () => {
    render(<TaskConfigForm onSubmit={vi.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText(/遮蔽類型/i), 'replace');

    expect(screen.getByLabelText(/替換文字/i)).toBeInTheDocument();
  });
});
```

---

## 檔案結構

```text
web/frontend/src/
├── domain/
│   └── value-objects/
│       └── schemas/
│           ├── taskConfigSchema.ts
│           ├── userSchema.ts
│           └── customValidators.ts
│
└── presentation/
    └── components/
        └── forms/
            ├── TaskConfigForm.tsx
            ├── LoginForm.tsx
            └── FileUploadForm.tsx
```

---

## 檢查清單

建立表單時必須：

- [ ] 使用 Zod 定義 Schema (在 domain/value-objects/schemas/)
- [ ] 使用 zodResolver 連接 React Hook Form
- [ ] 處理所有錯誤訊息顯示
- [ ] 實作 isSubmitting 狀態防止重複送出
- [ ] 條件欄位使用 watch() 監聽
- [ ] 建立對應測試檔案

---

## 輸出格式

```text
📝 表單驗證建立完成

Schema：domain/value-objects/schemas/taskConfigSchema.ts
元件：presentation/components/forms/TaskConfigForm.tsx

✅ 驗證規則
  └─ taskName: 必填, 1-100 字
  └─ maskingType: 枚舉 (redact|replace|tag)
  └─ confidence: 數字, 0.5-1.0
  └─ 條件驗證: replace 模式需要 customReplacement

📦 使用的套件
  └─ react-hook-form: ^7.x
  └─ @hookform/resolvers: ^3.x
  └─ zod: ^3.x

🧪 測試建議
  └─ 驗證錯誤顯示
  └─ 有效表單送出
  └─ 條件欄位顯示
```

```
