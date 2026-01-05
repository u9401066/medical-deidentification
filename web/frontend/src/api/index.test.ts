import { describe, it, expect, vi } from 'vitest'
import api from './index'

describe('API', () => {
  describe('healthCheck', () => {
    it('should return health status', async () => {
      const result = await api.healthCheck()
      
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('timestamp')
      expect(result).toHaveProperty('llm')
      expect(result.llm?.status).toBe('online')
    })
  })

  describe('listFiles', () => {
    it('should return file list', async () => {
      const files = await api.listFiles()
      
      expect(Array.isArray(files)).toBe(true)
      expect(files.length).toBeGreaterThan(0)
      expect(files[0]).toHaveProperty('id')
      expect(files[0]).toHaveProperty('filename')
      expect(files[0]).toHaveProperty('file_type')
    })

    it('should map file_id to id', async () => {
      const files = await api.listFiles()
      
      // 確認每個檔案都有 id 屬性
      files.forEach(file => {
        expect(file.id).toBeDefined()
      })
    })
  })

  describe('previewFile', () => {
    it('should return preview data', async () => {
      const preview = await api.previewFile('file-001')
      
      expect(preview).toHaveProperty('type')
      expect(preview).toHaveProperty('columns')
      expect(preview).toHaveProperty('data')
      expect(preview).toHaveProperty('total_rows')
      expect(preview).toHaveProperty('page')
    })

    it('should support pagination', async () => {
      const preview = await api.previewFile('file-001', 1, 10)
      
      expect(preview.page).toBe(1)
      expect(preview.page_size).toBeDefined()
    })
  })

  describe('listTasks', () => {
    it('should return task list', async () => {
      const tasks = await api.listTasks()
      
      expect(Array.isArray(tasks)).toBe(true)
      expect(tasks.length).toBeGreaterThan(0)
      expect(tasks[0]).toHaveProperty('task_id')
      expect(tasks[0]).toHaveProperty('status')
      expect(tasks[0]).toHaveProperty('progress')
    })

    it('should have timing info for processing tasks', async () => {
      const tasks = await api.listTasks()
      const processingTask = tasks.find(t => t.status === 'processing')
      
      if (processingTask) {
        expect(processingTask.elapsed_seconds).toBeDefined()
      }
    })
  })

  describe('startProcessing', () => {
    it('should create a new task', async () => {
      const result = await api.startProcessing({
        file_ids: ['file-001'],
        config: { masking_type: 'mask' },
        job_name: 'Test Job',
      })
      
      expect(result).toHaveProperty('task_id')
      expect(result.status).toBe('pending')
    })
  })

  describe('getResults', () => {
    it('should return results list', async () => {
      const results = await api.getResults()
      
      expect(Array.isArray(results)).toBe(true)
    })
  })

  describe('getResultDetail', () => {
    it('should return detailed result', async () => {
      const detail = await api.getResultDetail('task-001')
      
      expect(detail).toHaveProperty('task_id')
      expect(detail).toHaveProperty('results')
      expect(detail).toHaveProperty('config')
      expect(detail.results).toBeInstanceOf(Array)
    })

    it('should include PHI entities', async () => {
      const detail = await api.getResultDetail('task-001')
      
      if (detail.results.length > 0) {
        const result = detail.results[0]
        expect(result).toHaveProperty('phi_entities')
        expect(result.phi_entities).toBeInstanceOf(Array)
      }
    })
  })

  describe('getPHITypes', () => {
    it('should return PHI types', async () => {
      const types = await api.getPHITypes()
      
      expect(Array.isArray(types)).toBe(true)
      expect(types.length).toBeGreaterThan(0)
      expect(types[0]).toHaveProperty('type')
      expect(types[0]).toHaveProperty('display_name')
    })
  })

  describe('getConfig', () => {
    it('should return config', async () => {
      const config = await api.getConfig()
      
      expect(config).toHaveProperty('enabled')
      expect(config).toHaveProperty('default_masking')
    })
  })

  describe('updateConfig', () => {
    it('should update config', async () => {
      const newConfig = { enabled: true, strict_mode: true }
      const result = await api.updateConfig(newConfig)
      
      expect(result).toHaveProperty('message')
      expect(result).toHaveProperty('config')
    })
  })
})
