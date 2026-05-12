/**
 * E2E 測試：側邊欄 - 檔案上傳、檔案列表、LLM 狀態
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes, mockFiles } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
})

test.describe('側邊欄 - 檔案管理', () => {
  test('應顯示上傳區域', async ({ page }) => {
    await expect(page.getByText('上傳檔案並處理敏感資料')).toBeVisible()
  })

  test('應顯示已上傳的檔案列表', async ({ page }) => {
    for (const file of mockFiles) {
      await expect(
        page.getByRole('paragraph').filter({ hasText: file.filename })
      ).toBeVisible()
    }
  })

  test('應顯示檔案數量', async ({ page }) => {
    await expect(page.getByText(`已上傳檔案 (${mockFiles.length})`)).toBeVisible()
  })

  test('應顯示 LLM 狀態指示器', async ({ page }) => {
    await expect(page.getByText(/^在線 \(qwen2\.5:1\.5b\)$/)).toBeVisible()
  })

  test('點擊檔案可選取', async ({ page }) => {
    const fileItem = page.getByRole('paragraph').filter({ hasText: mockFiles[0].filename })
    await fileItem.click()
    const previewTab = page.getByRole('tab', { name: /資料預覽/ })
    await expect(previewTab).toHaveAttribute('data-state', 'active')
  })
})

test.describe('側邊欄 - 操作按鈕', () => {
  test('應顯示處理與下載按鈕', async ({ page }) => {
    await expect(page.getByRole('button', { name: /開始處理|處理/ })).toBeVisible()
  })
})
