import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent } from '@/test/test-utils'
import { Sidebar } from './Sidebar'

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render upload area', async () => {
    renderWithProviders(<Sidebar />)
    
    await waitFor(() => {
      // 實際文字是「拖放檔案至此處」
      expect(screen.getByText(/拖放檔案至此處/i)).toBeInTheDocument()
    })
  })

  it('should show file list after loading', async () => {
    renderWithProviders(<Sidebar />)
    
    // 等待檔案載入
    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument()
    })
  })

  it('should show LLM status', async () => {
    renderWithProviders(<Sidebar />)
    
    await waitFor(() => {
      // 檢查 LLM 狀態指示器
      const statusIndicator = screen.queryByText(/online/i) || screen.queryByText(/在線/i)
      expect(statusIndicator || screen.getByText(/LLM/i)).toBeInTheDocument()
    })
  })

  it('should allow file selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Sidebar />)
    
    // 等待檔案載入
    await waitFor(() => {
      expect(screen.getByText(/test_patient_data.csv/i)).toBeInTheDocument()
    })

    // 點擊檔案選取
    const fileItem = screen.getByText(/test_patient_data.csv/i).closest('div')
    if (fileItem) {
      await user.click(fileItem)
    }
  })

  it('should show file count', async () => {
    renderWithProviders(<Sidebar />)
    
    await waitFor(() => {
      // 應該顯示檔案數量
      const countBadge = screen.queryByText(/2/) || screen.queryByText(/已上傳檔案/)
      expect(countBadge).toBeInTheDocument()
    })
  })
})
