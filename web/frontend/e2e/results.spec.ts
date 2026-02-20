/**
 * E2E 測試：處理結果面板
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
  await page.getByRole('tab', { name: /處理結果/ }).click()
})

test.describe('處理結果面板', () => {
  test('應顯示結果列表', async ({ page }) => {
    // ResultsPanel 顯示 filenames (不是 job_name)
    await expect(page.getByText('test_patient_data.csv').first()).toBeVisible()
  })

  test('應顯示 PHI 偵測計數', async ({ page }) => {
    await expect(page.getByText('15').first()).toBeVisible()
  })

  test('應顯示結果數量', async ({ page }) => {
    await expect(page.getByText(/1 筆結果/)).toBeVisible()
  })

  test('點擊結果可查看詳情', async ({ page }) => {
    // 點擊結果卡片
    const resultCard = page.getByText('test_patient_data.csv').first()
    await resultCard.click()

    // 點擊後應顯示詳情區塊（原始文本或處理後文本）
    await expect(
      page.getByText(/原始文本|處理後文本|PHI|詳情/).first()
    ).toBeVisible({ timeout: 10000 })
  })

  test('結果清單無結果時應顯示空狀態', async ({ page }) => {
    await page.route('**/api/results', (route) =>
      route.fulfill({ json: [] })
    )
    await page.goto('/')
    await page.getByRole('tab', { name: /處理結果/ }).click()

    await expect(page.getByText('尚無處理結果')).toBeVisible()
  })
})
