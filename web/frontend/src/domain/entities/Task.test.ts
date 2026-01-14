/**
 * Task Entity Tests
 */
import { describe, it, expect } from 'vitest';
import {
  createTask,
  isTaskCompleted,
  isTaskProcessing,
  isTaskFailed,
  formatTaskTime,
} from './Task';

describe('Task Entity', () => {
  const mockTaskData = {
    task_id: 'task-123',
    status: 'processing',
    progress: 50,
    message: 'Processing...',
    created_at: '2026-01-14T10:00:00Z',
    started_at: '2026-01-14T10:00:01Z',
    elapsed_seconds: 30,
    estimated_remaining_seconds: 30,
    processing_speed: 100,
    total_chars: 6000,
    processed_chars: 3000,
  };

  describe('createTask', () => {
    it('should create a Task entity from API response', () => {
      const task = createTask(mockTaskData);

      expect(task.id).toBe('task-123');
      expect(task.status).toBe('processing');
      expect(task.progress).toBe(50);
      expect(task.message).toBe('Processing...');
      expect(task.createdAt).toBeInstanceOf(Date);
      expect(task.elapsedSeconds).toBe(30);
    });

    it('should handle optional fields', () => {
      const minimalData = {
        task_id: 'task-456',
        status: 'pending',
        progress: 0,
        message: 'Waiting...',
        created_at: '2026-01-14T10:00:00Z',
      };

      const task = createTask(minimalData);

      expect(task.id).toBe('task-456');
      expect(task.completedAt).toBeUndefined();
      expect(task.startedAt).toBeUndefined();
    });
  });

  describe('isTaskCompleted', () => {
    it('should return true for completed tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'completed' });
      expect(isTaskCompleted(task)).toBe(true);
    });

    it('should return false for non-completed tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'processing' });
      expect(isTaskCompleted(task)).toBe(false);
    });
  });

  describe('isTaskProcessing', () => {
    it('should return true for processing tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'processing' });
      expect(isTaskProcessing(task)).toBe(true);
    });

    it('should return false for non-processing tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'completed' });
      expect(isTaskProcessing(task)).toBe(false);
    });
  });

  describe('isTaskFailed', () => {
    it('should return true for failed tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'failed' });
      expect(isTaskFailed(task)).toBe(true);
    });

    it('should return false for non-failed tasks', () => {
      const task = createTask({ ...mockTaskData, status: 'completed' });
      expect(isTaskFailed(task)).toBe(false);
    });
  });

  describe('formatTaskTime', () => {
    it('should return "計算中..." for undefined', () => {
      expect(formatTaskTime(undefined)).toBe('計算中...');
    });

    it('should return "計算中..." for negative values', () => {
      expect(formatTaskTime(-1)).toBe('計算中...');
    });

    it('should format seconds correctly', () => {
      expect(formatTaskTime(30)).toBe('30 秒');
      expect(formatTaskTime(59)).toBe('59 秒');
    });

    it('should format minutes correctly', () => {
      expect(formatTaskTime(60)).toBe('1 分 0 秒');
      expect(formatTaskTime(90)).toBe('1 分 30 秒');
      expect(formatTaskTime(3599)).toBe('59 分 59 秒');
    });

    it('should format hours correctly', () => {
      expect(formatTaskTime(3600)).toBe('1 小時 0 分');
      expect(formatTaskTime(7200)).toBe('2 小時 0 分');
      expect(formatTaskTime(3660)).toBe('1 小時 1 分');
    });
  });
});
