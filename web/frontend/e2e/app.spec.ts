/**
 * E2E 測試：主頁面佈局與標籤導航
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
})

test.describe('主頁面佈局', () => {
  test('應正確渲染側邊欄與主內容區', async ({ page }) => {
    // 側邊欄
    await expect(page.getByText('PHI 去識別化工具')).toBeVisible()
    // 主內容區應有標籤列
    await expect(page.getByRole('tab', { name: /使用說明/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /資料預覽/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /處理任務/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /處理結果/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /報告/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /設定/ })).toBeVisible()
  })

  test('預設顯示「使用說明」標籤', async ({ page }) => {
    const guideTab = page.getByRole('tab', { name: /使用說明/ })
    await expect(guideTab).toHaveAttribute('data-state', 'active')
  })

  test('點擊標籤可切換內容', async ({ page }) => {
    // 切到「處理任務」
    await page.getByRole('tab', { name: /處理任務/ }).click()
    const tasksTab = page.getByRole('tab', { name: /處理任務/ })
    await expect(tasksTab).toHaveAttribute('data-state', 'active')

    // 切到「設定」
    await page.getByRole('tab', { name: /設定/ }).click()
    const settingsTab = page.getByRole('tab', { name: /設定/ })
    await expect(settingsTab).toHaveAttribute('data-state', 'active')
  })

  test('主要工作流標籤都可切換', async ({ page }) => {
    const tabs = ['使用說明', '資料預覽', '處理任務', '處理結果', '報告', '設定']
    for (const tabName of tabs) {
      await page.getByRole('tab', { name: new RegExp(tabName) }).click()
      const tab = page.getByRole('tab', { name: new RegExp(tabName) })
      await expect(tab).toHaveAttribute('data-state', 'active')
    }
  })
})

test.describe('頁面基本可用性', () => {
  test('頁面在 3 秒內完成載入', async ({ page }) => {
    const start = Date.now()
    await page.goto('/')
    await page.getByRole('tab', { name: /使用說明/ }).waitFor()
    const elapsed = Date.now() - start
    expect(elapsed).toBeLessThan(3000)
  })

  test('頁面標題正確', async ({ page }) => {
    await expect(page).toHaveTitle(/醫療文本去識別化/)
  })

  test('沒有 console 錯誤', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })
    await page.goto('/')
    await page.waitForTimeout(1000)
    // 過濾掉 React 開發模式的非致命警告
    const criticalErrors = errors.filter(
      (e) => !e.includes('Warning:') && !e.includes('React does not recognize')
    )
    expect(criticalErrors).toHaveLength(0)
  })
})
