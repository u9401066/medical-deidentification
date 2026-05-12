import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { SettingsPanel } from './Settings'

describe('SettingsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should keep PHI settings visible but read-only for regular users', async () => {
    renderWithProviders(<SettingsPanel canEdit={false} />)

    expect(screen.getByRole('button', { name: /^PHI 設定$/i })).toBeInTheDocument()
    expect(screen.getByText(/一般使用者模式/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /法規管理/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /LLM 設定/i })).not.toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/^姓名$/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /僅可檢視/i })).toBeDisabled()
  })
})
