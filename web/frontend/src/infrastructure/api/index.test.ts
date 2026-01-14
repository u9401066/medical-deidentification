import { describe, it, expect } from 'vitest';
import api from './index';

describe('API', () => {
  describe('healthCheck', () => {
    it('should return health status', async () => {
      const result = await api.healthCheck();

      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('timestamp');
      expect(result).toHaveProperty('llm');
      expect(result.llm?.status).toBe('online');
    });
  });

  describe('listFiles', () => {
    it('should return file list', async () => {
      const files = await api.listFiles();

      expect(Array.isArray(files)).toBe(true);
      expect(files.length).toBeGreaterThan(0);
      expect(files[0]).toHaveProperty('id');
      expect(files[0]).toHaveProperty('filename');
      expect(files[0]).toHaveProperty('file_type');
    });

    it('should map file_id to id', async () => {
      const files = await api.listFiles();

      // 確認每個檔案都有 id 屬性
      files.forEach((file) => {
        expect(file.id).toBeDefined();
      });
    });
  });

  describe('previewFile', () => {
    it('should return preview data', async () => {
      const preview = await api.previewFile('file-001');

      expect(preview).toHaveProperty('type');
      expect(preview).toHaveProperty('columns');
      expect(preview).toHaveProperty('data');
      expect(preview).toHaveProperty('total_rows');
      expect(preview).toHaveProperty('page');
    });

    it('should support pagination', async () => {
      const preview = await api.previewFile('file-001', 1, 10);

      expect(preview.page).toBe(1);
      expect(preview.page_size).toBeDefined();
    });
  });

  describe('listTasks', () => {
    it('should return task list', async () => {
      const tasks = await api.listTasks();

      expect(Array.isArray(tasks)).toBe(true);
    });

    it('should have timing info for processing tasks', async () => {
      const tasks = await api.listTasks();
      const processingTask = tasks.find((t) => t.status === 'processing');

      if (processingTask) {
        expect(processingTask).toHaveProperty('elapsed_seconds');
        expect(processingTask).toHaveProperty('estimated_remaining_seconds');
      }
    });
  });

  describe('startProcessing', () => {
    it('should create a new task', async () => {
      const result = await api.startProcessing({
        file_ids: ['file-001'],
        config: { masking_type: 'mask' },
        job_name: 'Test Job',
      });

      expect(result).toHaveProperty('task_id');
      expect(result).toHaveProperty('status');
      // 初始狀態可能是 pending 或 processing
      expect(['pending', 'processing']).toContain(result.status);
    });
  });

  describe('getResults', () => {
    it('should return results list', async () => {
      const results = await api.getResults();

      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('getResultDetail', () => {
    it('should return detailed result', async () => {
      const detail = await api.getResultDetail('task-001');

      expect(detail).toHaveProperty('task_id');
      expect(detail).toHaveProperty('job_name');
      expect(detail).toHaveProperty('results');
    });

    it('should include PHI entities', async () => {
      const detail = await api.getResultDetail('task-001');

      if (detail.results?.[0]?.phi_entities) {
        const entity = detail.results[0].phi_entities[0];
        expect(entity).toHaveProperty('type');
        expect(entity).toHaveProperty('value');
        expect(entity).toHaveProperty('masked_value');
      }
    });
  });

  describe('getPHITypes', () => {
    it('should return PHI types', async () => {
      const types = await api.getPHITypes();

      expect(Array.isArray(types)).toBe(true);
      expect(types.length).toBeGreaterThan(0);
      expect(types[0]).toHaveProperty('type');
      expect(types[0]).toHaveProperty('display_name');
    });
  });

  describe('getConfig', () => {
    it('should return config', async () => {
      const config = await api.getConfig();

      expect(config).toHaveProperty('enabled');
      expect(config).toHaveProperty('default_masking');
    });
  });

  describe('updateConfig', () => {
    it('should update config', async () => {
      const result = await api.updateConfig({
        enabled: true,
        default_masking: 'mask',
      });

      expect(result).toHaveProperty('message');
      expect(result).toHaveProperty('config');
    });
  });
});
