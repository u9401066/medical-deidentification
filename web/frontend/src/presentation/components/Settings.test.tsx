import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { renderWithProviders, userEvent } from '@/test/test-utils'
import { server } from '@/test/mocks/server'
import { SettingsPanel } from './Settings'

describe('SettingsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should let regular users edit PHI settings without system-admin tabs', async () => {
    renderWithProviders(<SettingsPanel canEdit canEditSystem={false} />)

    expect(screen.getByRole('button', { name: /^PHI 設定$/i })).toBeInTheDocument()
    expect(screen.getByText(/自行調整本帳號的 PHI/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /法規管理/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /LLM 設定/i })).not.toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/^姓名$/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /儲存設定/i })).toBeEnabled()
  })

  it('should normalize legacy PHI type lists before saving user settings', async () => {
    const user = userEvent.setup()
    let savedPayload: Record<string, unknown> | undefined

    server.use(
      http.get('*/api/settings/config', () =>
        HttpResponse.json({
          enabled: true,
          strict_mode: false,
          default_masking: 'mask',
          preserve_format: true,
          phi_types: ['NAME', 'PHONE', 'EMAIL', 'ADDRESS', 'DATE'],
        })
      ),
      http.put('*/api/settings/config', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ message: 'Config updated', config: savedPayload })
      })
    )

    renderWithProviders(<SettingsPanel canEdit canEditSystem={false} />)

    await waitFor(() => {
      expect(screen.getByText(/^姓名$/i)).toBeInTheDocument()
    })

    const nameRow = screen.getByText(/^姓名$/i).closest('div')?.parentElement?.parentElement
    expect(nameRow).not.toBeNull()
    await user.click(within(nameRow!).getByRole('switch'))
    await user.click(screen.getByRole('button', { name: /儲存設定/i }))

    await waitFor(() => {
      const phiTypes = savedPayload?.phi_types as Record<string, unknown> | undefined
      expect(Array.isArray(phiTypes)).toBe(false)
      expect(phiTypes).not.toHaveProperty('0')
      expect(phiTypes).toEqual(
        expect.objectContaining({
          NAME: expect.objectContaining({ enabled: false, masking: 'mask' }),
          PHONE: expect.objectContaining({ enabled: true, masking: 'mask' }),
          DATE: expect.objectContaining({ enabled: true, masking: 'generalize' }),
        })
      )
    })
  })
})
