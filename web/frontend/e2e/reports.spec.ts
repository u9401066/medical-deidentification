/**
 * E2E 測試：報告面板
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
  await page.getByRole('tab', { name: /報告/ }).click()
})

test.describe('報告面板', () => {
  test('應顯示報告選擇下拉選單', async ({ page }) => {
    await expect(page.getByRole('combobox')).toBeVisible()
  })

  test('應顯示初始提示訊息', async ({ page }) => {
    await expect(page.getByText('請選擇報告以查看詳情')).toBeVisible()
  })

  test('選擇報告後顯示詳情', async ({ page }) => {
    // 打開下拉選單
    await page.getByRole('combobox').filter({ hasText: /選擇報告/ }).click()
    // 選擇報告項目
    await page.getByRole('option').first().click()
    // 等待詳情載入 — 應顯示報告概要
    await expect(page.getByText('報告概要')).toBeVisible({ timeout: 10000 })
    // 應顯示 PHI 數量
    await expect(page.getByText('15').first()).toBeVisible()
    // 應顯示處理時間
    await expect(page.getByText(/5\.5s/)).toBeVisible()
  })

  test('選擇報告後可匯出', async ({ page }) => {
    await page.getByRole('combobox').filter({ hasText: /選擇報告/ }).click()
    await page.getByRole('option').first().click()
    await expect(page.getByRole('button', { name: /匯出報告/ })).toBeVisible({ timeout: 10000 })
  })

  test('報告列表為空時應顯示空狀態', async ({ page }) => {
    await page.route('**/api/reports', (route) =>
      route.fulfill({ json: [] })
    )
    await page.goto('/')
    await page.getByRole('tab', { name: /報告/ }).click()
    await expect(page.getByText('尚無任何報告')).toBeVisible()
  })
})
