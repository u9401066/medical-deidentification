import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { TaskCard } from './TaskCard';
import { TaskStatus } from '@/infrastructure/api';

const mockProcessingTask: TaskStatus = {
  task_id: 'test-123-abc',
  status: 'processing',
  progress: 50,
  message: '處理中...',
  created_at: new Date().toISOString(),
  elapsed_seconds: 30,
  estimated_remaining_seconds: 25,
  processing_speed: 120.5,
};

const mockCompletedTask: TaskStatus = {
  task_id: 'test-456-def',
  status: 'completed',
  progress: 100,
  message: '處理完成',
  created_at: new Date().toISOString(),
  elapsed_seconds: 60,
  processing_speed: 150.0,
};

const mockFailedTask: TaskStatus = {
  task_id: 'test-789-ghi',
  status: 'failed',
  progress: 30,
  message: 'API 連線失敗',
  created_at: new Date().toISOString(),
};

describe('TaskCard', () => {
  it('should render processing task with progress', () => {
    renderWithProviders(<TaskCard task={mockProcessingTask} />);

    // 顯示任務 ID
    expect(screen.getByText(/test-123/)).toBeInTheDocument();
    // 顯示處理中狀態 Badge
    expect(screen.getAllByText(/處理中/).length).toBeGreaterThanOrEqual(1);
    // 顯示進度條
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    // 顯示訊息
    expect(screen.getByText('處理中...')).toBeInTheDocument();
  });

  it('should show time estimates for processing task', () => {
    renderWithProviders(<TaskCard task={mockProcessingTask} />);

    // 顯示已用時間
    expect(screen.getByText(/已用時/)).toBeInTheDocument();
    expect(screen.getByText(/30 秒/)).toBeInTheDocument();
    // 顯示剩餘時間
    expect(screen.getByText(/剩餘/)).toBeInTheDocument();
    // 顯示處理速度
    expect(screen.getByText(/120.5 字元\/秒/)).toBeInTheDocument();
  });

  it('should render completed task', () => {
    renderWithProviders(<TaskCard task={mockCompletedTask} />);

    expect(screen.getByText(/test-456/)).toBeInTheDocument();
    // 完成 Badge 存在
    expect(screen.getAllByText(/完成/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/✓ 耗時/)).toBeInTheDocument();
  });

  it('should render failed task', () => {
    renderWithProviders(<TaskCard task={mockFailedTask} />);

    expect(screen.getByText(/test-789/)).toBeInTheDocument();
    // 失敗 Badge 存在
    expect(screen.getAllByText(/失敗/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('API 連線失敗')).toBeInTheDocument();
  });

  it('should show created timestamp', () => {
    renderWithProviders(<TaskCard task={mockProcessingTask} />);

    expect(screen.getByText(/建立:/)).toBeInTheDocument();
  });
});
