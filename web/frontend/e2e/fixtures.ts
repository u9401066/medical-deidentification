/**
 * E2E 測試共用 Mock 資料與路由攔截
 *
 * 使用 Playwright route API 攔截 /api/* 請求並回傳 mock 資料，
 * 讓 E2E 測試不依賴真實後端服務。
 */
import { type Page } from '@playwright/test'

// ============================================================
// Mock Data
// ============================================================

export const mockFiles = [
  {
    file_id: 'file-001',
    id: 'file-001',
    filename: 'test_patient_data.csv',
    size: 1024,
    upload_time: '2025-12-31T10:00:00',
    file_type: 'csv',
    preview_available: true,
    status: 'pending',
    task_id: null,
  },
  {
    file_id: 'file-002',
    id: 'file-002',
    filename: 'medical_records.xlsx',
    size: 2048,
    upload_time: '2025-12-31T11:00:00',
    file_type: 'xlsx',
    preview_available: true,
    status: 'pending',
    task_id: null,
  },
]

export const mockTasks = [
  {
    task_id: 'task-001',
    status: 'completed',
    progress: 100,
    message: '處理完成',
    file_ids: ['file-001'],
    created_at: '2025-12-31T10:00:00',
    completed_at: '2025-12-31T10:05:00',
    elapsed_seconds: 300,
  },
  {
    task_id: 'task-002',
    status: 'processing',
    progress: 45,
    message: '處理中...',
    file_ids: ['file-002'],
    created_at: '2025-12-31T11:00:00',
    elapsed_seconds: 120,
    estimated_remaining_seconds: 150,
  },
]

export const mockResults = [
  {
    task_id: 'task-001',
    job_name: '測試任務',
    files_count: 1,
    filenames: ['test_patient_data.csv'],
    total_phi_found: 15,
    phi_by_type: { NAME: 5, PHONE: 5, EMAIL: 5 },
    processed_at: '2025-12-31T10:05:00',
  },
]

export const mockResultDetail = {
  task_id: 'task-001',
  job_name: '測試任務',
  config: { masking_type: 'mask', phi_types: ['NAME', 'PHONE', 'EMAIL'] },
  results: [
    {
      file_id: 'file-001',
      filename: 'test_patient_data.csv',
      phi_found: 15,
      rows_processed: 100,
      status: 'completed',
      phi_by_type: { NAME: 5, PHONE: 5, EMAIL: 5 },
      phi_entities: [
        { type: 'NAME', value: 'John Smith', masked_value: '[MASKED]', confidence: 0.95 },
        { type: 'PHONE', value: '0912-345-678', masked_value: '[MASKED]', confidence: 0.98 },
        { type: 'EMAIL', value: 'john@example.com', masked_value: '[MASKED]', confidence: 0.99 },
      ],
      original_data: [
        { name: 'John Smith', phone: '0912-345-678', email: 'john@example.com' },
      ],
      masked_data: [
        { name: '[MASKED]', phone: '[MASKED]', email: '[MASKED]' },
      ],
    },
  ],
  processed_at: '2025-12-31T10:05:00',
}

export const mockReports = [
  {
    id: 'report-001',
    filename: 'task-001_report.json',
    task_id: 'task-001',
    job_name: '測試任務',
    files_processed: 1,
    total_phi_found: 15,
    created_at: '2025-12-31T10:05:00',
  },
]

export const mockReportDetail = {
  id: 'report-001',
  task_id: 'task-001',
  job_name: '測試任務',
  generated_at: '2025-12-31T10:05:00',
  summary: {
    files_processed: 1,
    total_phi_found: 15,
    total_chars: 5000,
    processing_time_seconds: 5.5,
    processing_speed_chars_per_sec: 909,
  },
  file_details: [
    {
      file_id: 'file-001',
      filename: 'test_patient_data.csv',
      phi_found: 15,
      phi_by_type: { NAME: 5, PHONE: 5, EMAIL: 5 },
      rows_processed: 100,
      status: 'completed',
    },
  ],
}

export const mockHealth = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  llm: {
    status: 'online',
    model: 'qwen2.5:1.5b',
    provider: 'ollama',
    endpoint: 'http://localhost:11434',
  },
  engine_available: true,
}

export const mockPHITypes = [
  { type: 'NAME', display_name: '姓名', description: '個人姓名', category: 'identity', default_masking: 'mask' },
  { type: 'PHONE', display_name: '電話', description: '電話號碼', category: 'contact', default_masking: 'mask' },
  { type: 'EMAIL', display_name: 'Email', description: '電子郵件', category: 'contact', default_masking: 'mask' },
  { type: 'ADDRESS', display_name: '地址', description: '住址', category: 'contact', default_masking: 'mask' },
  { type: 'DATE', display_name: '日期', description: '出生日期等', category: 'demographic', default_masking: 'generalize' },
]

export const mockConfig = {
  enabled: true,
  strict_mode: false,
  default_masking: 'mask',
  preserve_format: true,
}

export const mockRegulations = [
  {
    id: 'hipaa',
    name: 'HIPAA',
    description: 'US Health Insurance Portability and Accountability Act',
    phi_types: ['NAME', 'PHONE', 'EMAIL'],
    source: 'US',
    enabled: true,
    rules_count: 18,
  },
]

export const mockPreviewData = {
  type: 'tabular',
  columns: ['name', 'phone', 'email'],
  data: [
    { name: 'John Smith', phone: '0912-345-678', email: 'john@example.com' },
    { name: 'Jane Doe', phone: '0923-456-789', email: 'jane@example.com' },
  ],
  total_rows: 100,
  page: 1,
  page_size: 20,
  has_more: true,
}

export const mockLLMStatus = {
  online: true,
  provider: 'ollama',
  endpoint: 'http://localhost:11434',
  current_model: 'qwen2.5:1.5b',
  available_models: [
    { name: 'qwen2.5:1.5b', size: '1.5B' },
    { name: 'llama3.3:70b', size: '70B' },
  ],
}

export const mockLLMConfig = {
  provider: 'ollama',
  base_url: 'http://localhost:11434',
  model: 'qwen2.5:1.5b',
  temperature: 0.1,
  max_tokens: 4096,
  timeout: 120,
}

export const mockLLMProviders = [
  { id: 'ollama', name: 'Ollama', description: 'Local LLM', requires_api_key: false, default_url: 'http://localhost:11434' },
  { id: 'openai', name: 'OpenAI', description: 'OpenAI API', requires_api_key: true, default_url: 'https://api.openai.com/v1' },
]

// ============================================================
// Route Setup Helper
// ============================================================

/**
 * 為 Playwright page 設定所有 API mock 路由
 */
export async function setupMockRoutes(page: Page) {
  // Health
  await page.route('**/api/health', (route) =>
    route.fulfill({ json: mockHealth })
  )

  // Files
  await page.route('**/api/files', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({ json: mockFiles })
    }
    return route.continue()
  })

  await page.route('**/api/upload', (route) =>
    route.fulfill({
      json: {
        file_id: `file-${Date.now()}`,
        id: `file-${Date.now()}`,
        filename: 'uploaded_file.csv',
        size: 1024,
        upload_time: new Date().toISOString(),
        file_type: 'csv',
        preview_available: true,
        status: 'pending',
      },
    })
  )

  await page.route('**/api/files/*', (route) => {
    if (route.request().method() === 'DELETE') {
      return route.fulfill({ json: { message: 'File deleted' } })
    }
    return route.continue()
  })

  // Preview
  await page.route('**/api/preview/*', (route) =>
    route.fulfill({ json: mockPreviewData })
  )

  // Processing
  await page.route('**/api/process', (route) =>
    route.fulfill({
      json: {
        task_id: `task-${Date.now()}`,
        status: 'pending',
        progress: 0,
        message: '任務已建立',
        created_at: new Date().toISOString(),
      },
    })
  )

  // Tasks
  await page.route('**/api/tasks', (route) =>
    route.fulfill({ json: mockTasks })
  )
  await page.route('**/api/tasks/*', (route) =>
    route.fulfill({ json: mockTasks[0] })
  )

  // Results
  await page.route('**/api/results', (route) =>
    route.fulfill({ json: mockResults })
  )
  await page.route('**/api/results/*', (route) =>
    route.fulfill({ json: mockResultDetail })
  )

  // Reports
  await page.route('**/api/reports', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({ json: mockReports })
    }
    return route.continue()
  })
  await page.route('**/api/reports/*/export*', (route) =>
    route.fulfill({
      body: 'exported data',
      headers: { 'Content-Type': 'application/octet-stream' },
    })
  )
  await page.route('**/api/reports/*', (route) =>
    route.fulfill({ json: mockReportDetail })
  )

  // Settings
  await page.route('**/api/settings/phi-types', (route) =>
    route.fulfill({ json: { phi_types: mockPHITypes } })
  )
  await page.route('**/api/settings/config', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({ json: mockConfig })
    }
    // PUT
    return route.fulfill({ json: { message: 'Config updated', config: mockConfig } })
  })

  // Regulations
  await page.route('**/api/regulations', (route) =>
    route.fulfill({ json: mockRegulations })
  )
  await page.route('**/api/regulations/*/content', (route) =>
    route.fulfill({ json: { id: 'hipaa', name: 'HIPAA', content: 'HIPAA regulation content...' } })
  )
  await page.route('**/api/regulations/upload', (route) =>
    route.fulfill({ json: { message: 'Uploaded', rules: mockRegulations } })
  )

  // LLM
  await page.route('**/api/llm/status', (route) =>
    route.fulfill({ json: mockLLMStatus })
  )
  await page.route('**/api/llm/config', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({ json: mockLLMConfig })
    }
    return route.fulfill({ json: { message: 'Updated', config: mockLLMConfig } })
  })
  await page.route('**/api/llm/model', (route) =>
    route.fulfill({ json: { message: 'Model set', config: mockLLMConfig } })
  )
  await page.route('**/api/llm/test', (route) =>
    route.fulfill({ json: { success: true, provider: 'ollama', model: 'qwen2.5:1.5b' } })
  )
  await page.route('**/api/llm/providers', (route) =>
    route.fulfill({ json: mockLLMProviders })
  )
  await page.route('**/api/llm/models', (route) =>
    route.fulfill({ json: mockLLMStatus.available_models })
  )

  // Download
  await page.route('**/api/download/*', (route) =>
    route.fulfill({
      body: 'file content',
      headers: { 'Content-Type': 'application/octet-stream' },
    })
  )
}
