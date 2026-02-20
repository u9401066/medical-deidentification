/**
 * E2E 測試：設定面板 - PHI 設定、法規管理、LLM 設定
 */
import { test, expect } from '@playwright/test'
import { setupMockRoutes, mockPHITypes } from './fixtures'

test.beforeEach(async ({ page }) => {
  await setupMockRoutes(page)
  await page.goto('/')
  await page.getByRole('tab', { name: /設定/ }).click()
})

test.describe('設定 - 頁籤切換', () => {
  test('應顯示三個子頁籤', async ({ page }) => {
    await expect(page.getByText('PHI 設定')).toBeVisible()
    await expect(page.getByText('法規管理')).toBeVisible()
    await expect(page.getByText('LLM 設定')).toBeVisible()
  })

  test('預設為 PHI 設定頁籤', async ({ page }) => {
    await expect(page.getByText('全域設定')).toBeVisible()
  })

  test('點擊可切換到法規管理', async ({ page }) => {
    await page.getByText('法規管理').click()
    await expect(page.getByRole('heading', { name: /上傳法規文件/ })).toBeVisible()
  })

  test('點擊可切換到 LLM 設定', async ({ page }) => {
    await page.getByText('LLM 設定').click()
    await expect(page.getByText(/LLM 連線狀態/)).toBeVisible()
  })
})

test.describe('設定 - PHI 設定', () => {
  test('應顯示啟用 PHI 偵測開關', async ({ page }) => {
    await expect(page.getByText('啟用 PHI 偵測')).toBeVisible()
  })

  test('應顯示嚴格模式開關', async ({ page }) => {
    await expect(page.getByText('嚴格模式')).toBeVisible()
  })

  test('應顯示預設遮蔽方式選擇', async ({ page }) => {
    await expect(page.getByText('預設遮蔽方式')).toBeVisible()
  })

  test('應顯示儲存按鈕', async ({ page }) => {
    await expect(page.getByRole('button', { name: /儲存設定/ })).toBeVisible()
  })

  test('應顯示所有 PHI 類型', async ({ page }) => {
    for (const phiType of mockPHITypes) {
      await expect(page.getByText(phiType.display_name).first()).toBeVisible()
    }
  })

  test('PHI 類型應有開關和遮蔽方式選擇', async ({ page }) => {
    // 每個 PHI 類型都有 switch 和 select
    const switches = page.locator('[role="switch"]')
    // 至少有 全域啟用(1) + 嚴格模式(1) + PHI 類型(5) = 7 個
    await expect(switches.first()).toBeVisible()
    const count = await switches.count()
    expect(count).toBeGreaterThanOrEqual(7)
  })

  test('儲存按鈕可點擊', async ({ page }) => {
    const saveButton = page.getByRole('button', { name: /儲存設定/ })
    await saveButton.click()
    // 不應出錯
    await expect(saveButton).toBeVisible()
  })
})

test.describe('設定 - 法規管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.getByText('法規管理').click()
  })

  test('應顯示上傳區域', async ({ page }) => {
    await expect(page.getByRole('button', { name: /選擇檔案/ })).toBeVisible()
  })

  test('應顯示已載入法規數量', async ({ page }) => {
    await expect(page.getByText(/已載入法規.*1/)).toBeVisible()
  })

  test('應顯示 HIPAA 法規', async ({ page }) => {
    await expect(page.getByText('HIPAA')).toBeVisible()
  })

  test('法規項目應有啟用/停用開關', async ({ page }) => {
    await expect(page.getByText(/啟用中/).first()).toBeVisible()
  })

  test('點擊查看內容按鈕可展開', async ({ page }) => {
    await page.getByRole('button', { name: /查看內容/ }).click()
    await expect(
      page.getByText(/HIPAA regulation content|收起/).first()
    ).toBeVisible()
  })

  test('支援的檔案格式應正確顯示', async ({ page }) => {
    await expect(page.getByText('支援 Markdown, TXT, PDF 格式')).toBeVisible()
  })
})

test.describe('設定 - LLM 設定', () => {
  test.beforeEach(async ({ page }) => {
    await page.getByText('LLM 設定').click()
  })

  test('應顯示連線狀態', async ({ page }) => {
    await expect(page.getByText(/線上/)).toBeVisible()
  })

  test('應顯示目前模型名稱', async ({ page }) => {
    await expect(page.getByText('qwen2.5:1.5b').first()).toBeVisible()
  })

  test('應顯示重新檢查按鈕', async ({ page }) => {
    await expect(page.getByRole('button', { name: /重新檢查/ })).toBeVisible()
  })

  test('應顯示測試連線按鈕', async ({ page }) => {
    await expect(page.getByRole('button', { name: /測試連線/ })).toBeVisible()
  })

  test('測試連線功能正常', async ({ page }) => {
    await page.getByRole('button', { name: /測試連線/ }).click()
    // 等待結果
    await expect(page.getByText(/連線成功/).first()).toBeVisible({ timeout: 5000 })
  })

  test('應顯示連線設定表單', async ({ page }) => {
    await expect(page.getByText('連線設定')).toBeVisible()
    await expect(page.getByText('服務提供者')).toBeVisible()
    await expect(page.getByText('API 端點')).toBeVisible()
    await expect(page.getByText('Temperature')).toBeVisible()
    await expect(page.getByText('Max Tokens')).toBeVisible()
    await expect(page.getByText(/Timeout/)).toBeVisible()
  })

  test('應顯示模型選擇區域', async ({ page }) => {
    await expect(page.getByText('模型選擇')).toBeVisible()
  })

  test('LLM 離線時應顯示離線狀態', async ({ page }) => {
    await page.route('**/api/llm/status', (route) =>
      route.fulfill({
        json: {
          online: false,
          provider: 'ollama',
          endpoint: 'http://localhost:11434',
          available_models: [],
          error: '無法連線到 Ollama 服務',
        },
      })
    )
    await page.goto('/')
    await page.getByRole('tab', { name: /設定/ }).click()
    await page.getByText('LLM 設定').click()

    await expect(page.getByText(/離線/)).toBeVisible()
  })
})
