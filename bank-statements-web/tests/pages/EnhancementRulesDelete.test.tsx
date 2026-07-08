import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApiProvider } from '@/api/ApiContext'
import { ErrorProvider } from '@/context/ErrorContext'
import { createMockApiClient } from '../createMockApiClient'
import { EnhancementRules } from '@/pages/EnhancementRules'
import { EnhancementRule, EnhancementRuleSource, MatchType } from '@/types/EnhancementRule'

const rule: EnhancementRule = {
  id: 'r1',
  patterns: [{ id: 'p1', normalized_description: 'netflix', match_type: MatchType.INFIX, sort_order: 0 }],
  source: EnhancementRuleSource.MANUAL,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  rule_type: 'Category Only',
}

const renderPage = () => {
  const apiClient = createMockApiClient()
  apiClient.enhancementRules.getAll = vi.fn().mockResolvedValue({ rules: [rule], total: 1 })
  const deleteRule = vi.fn().mockResolvedValue(undefined)
  apiClient.enhancementRules.delete = deleteRule

  const user = userEvent.setup()
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ApiProvider client={apiClient}>
          <ErrorProvider>
            <EnhancementRules />
          </ErrorProvider>
        </ApiProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
  return { deleteRule, user }
}

describe('EnhancementRules delete confirmation', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => cleanup())

  test('clicking delete asks for confirmation instead of deleting immediately', async () => {
    const { deleteRule, user } = renderPage()

    await user.click(await screen.findByTitle('Delete rule'))

    expect(await screen.findByText('Delete Enhancement Rule')).toBeInTheDocument()
    expect(deleteRule).not.toHaveBeenCalled()
  })

  test('cancelling the confirmation does not delete', async () => {
    const { deleteRule, user } = renderPage()

    await user.click(await screen.findByTitle('Delete rule'))
    await screen.findByText('Delete Enhancement Rule')
    await user.click(screen.getByRole('button', { name: /cancel/i }))

    await waitFor(() => expect(screen.queryByText('Delete Enhancement Rule')).not.toBeInTheDocument())
    expect(deleteRule).not.toHaveBeenCalled()
  })

  test('confirming deletes the rule', async () => {
    const { deleteRule, user } = renderPage()

    await user.click(await screen.findByTitle('Delete rule'))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: /^delete$/i }))

    await waitFor(() => expect(deleteRule).toHaveBeenCalledWith('r1'))
  })
})
