/**
 * E2E 測試：資料預覽面板
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes, mockFiles } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
  await page.getByRole('tab', { name: /資料預覽/ }).click()
})

test.describe('資料預覽面板', () => {
  test('切換後為資料預覽標籤', async ({ page }) => {
    const tab = page.getByRole('tab', { name: /資料預覽/ })
    await expect(tab).toHaveAttribute('data-state', 'active')
  })

  test('選取檔案後應顯示預覽資料', async ({ page }) => {
    // 點擊側邊欄的檔案（用段落選取器避免與 combobox 衝突）
    await page.getByRole('paragraph').filter({ hasText: mockFiles[0].filename }).click()

    // 應顯示表格資料
    await expect(
      page.getByText('John Smith').first()
    ).toBeVisible({ timeout: 10000 })
  })

  test('選取檔案後應顯示欄位名稱', async ({ page }) => {
    await page.getByRole('paragraph').filter({ hasText: mockFiles[0].filename }).click()

    await expect(
      page.getByText('name').first()
    ).toBeVisible({ timeout: 10000 })
  })

  test('進入資料預覽時會自動選取第一個可預覽檔案', async ({ page }) => {
    await expect(page.getByText(mockFiles[0].filename).first()).toBeVisible()
    await expect(page.getByText('John Smith').first()).toBeVisible({ timeout: 10000 })
  })
})
