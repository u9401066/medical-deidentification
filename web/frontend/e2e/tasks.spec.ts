/**
 * E2E 測試：處理任務面板
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
  await page.getByRole('tab', { name: /處理任務/ }).click()
})

test.describe('處理任務面板', () => {
  test('應顯示任務列表', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /task-001/ })).toBeVisible()
  })

  test('應顯示完成的任務狀態', async ({ page }) => {
    await expect(page.getByText(/completed|完成/).first()).toBeVisible()
  })

  test('應顯示處理中的任務狀態', async ({ page }) => {
    await expect(page.getByText(/processing|處理中/).first()).toBeVisible()
  })

  test('應顯示進度條', async ({ page }) => {
    // 進度條 (45% 的任務)
    const progressElements = page.locator('[role="progressbar"], .bg-primary, [class*="progress"]')
    await expect(progressElements.first()).toBeVisible()
  })

  test('應顯示重新整理按鈕', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /重新整理|重新載入|refresh|更新/ })
        .or(page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /refresh|重新/i }))
    ).toBeVisible()
  })

  test('已完成的任務應顯示耗時資訊', async ({ page }) => {
    // 300 秒 = 5 分鐘
    await expect(page.getByText(/300|5.*分|5:00/).first()).toBeVisible()
  })
})
