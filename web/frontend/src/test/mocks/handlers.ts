import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000/api'

// 模擬檔案資料
const mockFiles = [
  {
    file_id: 'file-001',
    filename: 'test_patient_data.csv',
    size: 1024,
    upload_time: '2025-12-31T10:00:00',
    file_type: 'csv',
    preview_available: true,
  },
  {
    file_id: 'file-002',
    filename: 'medical_records.xlsx',
    size: 2048,
    upload_time: '2025-12-31T11:00:00',
    file_type: 'xlsx',
    preview_available: true,
  },
]

// 模擬任務資料
const mockTasks = [
  {
    task_id: 'task-001',
    status: 'completed',
    progress: 100,
    message: '處理完成',
    created_at: '2025-12-31T10:00:00',
    completed_at: '2025-12-31T10:05:00',
    elapsed_seconds: 300,
  },
  {
    task_id: 'task-002',
    status: 'processing',
    progress: 45,
    message: '處理中...',
    created_at: '2025-12-31T11:00:00',
    elapsed_seconds: 120,
    estimated_remaining_seconds: 150,
  },
]

// 模擬結果資料
const mockResults = [
  {
    task_id: 'task-001',
    filename: 'test_patient_data.csv',
    phi_count: 15,
    status: 'completed',
    created_at: '2025-12-31T10:05:00',
  },
]

// 模擬結果詳情
const mockResultDetail = {
  task_id: 'task-001',
  job_name: '測試任務',
  config: {
    masking_type: 'mask',
    phi_types: ['NAME', 'PHONE', 'EMAIL'],
  },
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

// 模擬報告列表
const mockReports = [
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

// 模擬健康檢查
const mockHealth = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  llm: {
    status: 'online',
    model: 'qwen2.5:1.5b',
    provider: 'ollama',
  },
  engine_available: true,
}

// 模擬 PHI 類型
const mockPHITypes = [
  { type: 'NAME', display_name: '姓名', description: '個人姓名', category: 'identity', default_masking: 'mask' },
  { type: 'PHONE', display_name: '電話', description: '電話號碼', category: 'contact', default_masking: 'mask' },
  { type: 'EMAIL', display_name: 'Email', description: '電子郵件', category: 'contact', default_masking: 'mask' },
  { type: 'ADDRESS', display_name: '地址', description: '住址', category: 'contact', default_masking: 'mask' },
  { type: 'DATE', display_name: '日期', description: '出生日期等', category: 'demographic', default_masking: 'generalize' },
]

// 模擬設定
const mockConfig = {
  enabled: true,
  strict_mode: false,
  default_masking: 'mask',
  preserve_format: true,
}

export const handlers = [
  // ============ Health ============
  http.get(`${API_BASE}/health`, () => {
    return HttpResponse.json(mockHealth)
  }),

  // ============ Files ============
  http.get(`${API_BASE}/files`, () => {
    return HttpResponse.json(mockFiles)
  }),

  http.post(`${API_BASE}/upload`, async () => {
    const newFile = {
      file_id: `file-${Date.now()}`,
      filename: 'uploaded_file.csv',
      size: 1024,
      upload_time: new Date().toISOString(),
      file_type: 'csv',
      preview_available: true,
    }
    return HttpResponse.json(newFile)
  }),

  http.delete(`${API_BASE}/files/:fileId`, () => {
    return HttpResponse.json({ message: 'File deleted' })
  }),

  // ============ Preview ============
  http.get(`${API_BASE}/preview/:fileId`, () => {
    return HttpResponse.json({
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
    })
  }),

  // ============ Processing ============
  http.post(`${API_BASE}/process`, async () => {
    return HttpResponse.json({
      task_id: `task-${Date.now()}`,
      status: 'pending',
      progress: 0,
      message: '任務已建立',
      created_at: new Date().toISOString(),
    })
  }),

  // ============ Tasks ============
  http.get(`${API_BASE}/tasks`, () => {
    return HttpResponse.json(mockTasks)
  }),

  http.get(`${API_BASE}/tasks/:taskId`, ({ params }) => {
    const task = mockTasks.find((t) => t.task_id === params.taskId)
    if (task) {
      return HttpResponse.json(task)
    }
    return HttpResponse.json({ error: 'Task not found' }, { status: 404 })
  }),

  // ============ Results ============
  http.get(`${API_BASE}/results`, () => {
    return HttpResponse.json(mockResults)
  }),

  http.get(`${API_BASE}/results/:taskId`, ({ params }) => {
    if (params.taskId === 'task-001') {
      return HttpResponse.json(mockResultDetail)
    }
    return HttpResponse.json({ error: 'Result not found' }, { status: 404 })
  }),

  // ============ Reports ============
  http.get(`${API_BASE}/reports`, () => {
    return HttpResponse.json(mockReports)
  }),

  http.get(`${API_BASE}/reports/:taskId`, ({ params }) => {
    const report = mockReports.find((r) => r.task_id === params.taskId)
    if (report) {
      return HttpResponse.json({
        ...report,
        summary: { total_records: 100, phi_found: 15, phi_masked: 15, processing_time: 5.5 },
        phi_types: { NAME: 5, PHONE: 5, EMAIL: 5 },
        details: [
          { field: 'name', original: 'John Smith', masked: '[MASKED]', phi_type: 'NAME' },
        ],
      })
    }
    return HttpResponse.json({ error: 'Report not found' }, { status: 404 })
  }),

  // ============ Settings ============
  http.get(`${API_BASE}/settings/phi-types`, () => {
    return HttpResponse.json({ phi_types: mockPHITypes })
  }),

  http.get(`${API_BASE}/settings/config`, () => {
    return HttpResponse.json(mockConfig)
  }),

  http.put(`${API_BASE}/settings/config`, async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ message: 'Config updated', config: body })
  }),

  // ============ Regulations ============
  http.get(`${API_BASE}/regulations`, () => {
    return HttpResponse.json([
      { id: 'hipaa', name: 'HIPAA', description: 'US Health Insurance', phi_types: ['NAME'], source: 'US', enabled: true, rules_count: 18 },
    ])
  }),

  // ============ Download ============
  http.get(`${API_BASE}/download/:fileId`, () => {
    return new HttpResponse(new Blob(['test content'], { type: 'application/octet-stream' }))
  }),
]
