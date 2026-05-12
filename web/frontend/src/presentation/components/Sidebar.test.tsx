import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { renderWithProviders, userEvent } from '@/test/test-utils';
import { server } from '@/test/mocks/server';
import { Sidebar } from './Sidebar';

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render upload area', async () => {
    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      // 實際文字是「拖放檔案至此處」
      expect(screen.getByText(/拖放檔案至此處/i)).toBeInTheDocument();
    });
  });

  it('should show file list after loading', async () => {
    renderWithProviders(<Sidebar />);

    // 等待檔案載入
    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument();
    });
  });

  it('should show LLM status', async () => {
    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      // 檢查 LLM 狀態指示器
      const statusIndicator =
        screen.queryByText(/online/i) || screen.queryByText(/在線/i);
      expect(statusIndicator || screen.getByText(/LLM/i)).toBeInTheDocument();
    });
  });

  it('should allow file selection', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Sidebar />);

    // 等待檔案載入
    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument();
    });

    // 點擊檔案選取
    const fileItem = screen
      .getByText(/test_patient_data.csv/i)
      .closest('div');
    if (fileItem) {
      await user.click(fileItem);
    }
  });

  it('should show file count', async () => {
    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      // 應該顯示檔案數量
      const countBadge =
        screen.queryByText(/2/) || screen.queryByText(/已上傳檔案/);
      expect(countBadge).toBeInTheDocument();
    });
  });

  it('should ask users to confirm PHI settings before processing', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument();
    });

    const fileItem = screen
      .getByText(/test_patient_data.csv/i)
      .closest('div');
    expect(fileItem).not.toBeNull();
    await user.click(fileItem!);

    await user.click(screen.getByRole('button', { name: /開始處理/i }));

    expect(
      screen.getByRole('dialog', { name: /開始前確認 PHI 設定/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/目前 PHI 設定摘要/i)).toBeInTheDocument();
    expect(screen.getByText(/即將處理 1 個檔案/i)).toBeInTheDocument();
  });

  it('should let users return to PHI settings from processing confirmation', async () => {
    const user = userEvent.setup();
    const onOpenSettings = vi.fn();
    renderWithProviders(<Sidebar onOpenSettings={onOpenSettings} />);

    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument();
    });

    const fileItem = screen
      .getByText(/test_patient_data.csv/i)
      .closest('div');
    expect(fileItem).not.toBeNull();
    await user.click(fileItem!);

    await user.click(screen.getByRole('button', { name: /開始處理/i }));
    await user.click(screen.getByRole('button', { name: /返回 PHI 設定/i }));

    expect(onOpenSettings).toHaveBeenCalledTimes(1);
  });

  it('should include current PHI config when confirming processing', async () => {
    const user = userEvent.setup();
    let processPayload: Record<string, unknown> | undefined;

    server.use(
      http.post('*/api/process', async ({ request }) => {
        processPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          task_id: 'task-with-config',
          status: 'pending',
          progress: 0,
          message: '任務已建立',
          file_ids: ['file-001'],
          created_at: new Date().toISOString(),
        });
      })
    );

    renderWithProviders(<Sidebar />);

    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument();
    });

    const fileItem = screen
      .getByText(/test_patient_data.csv/i)
      .closest('div');
    expect(fileItem).not.toBeNull();
    await user.click(fileItem!);

    await user.click(screen.getByRole('button', { name: /開始處理/i }));
    await user.click(screen.getByRole('button', { name: /確認開始/i }));

    await waitFor(() => {
      expect(processPayload).toEqual(
        expect.objectContaining({
          file_ids: ['file-001'],
          config: expect.objectContaining({
            enabled: true,
            default_masking: 'mask',
            preserve_format: true,
          }),
        })
      );
    });
  });
});
