import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiProvider } from '@/api/ApiContext'
import { createMockApiClient } from '../createMockApiClient'
import { EnhancementRuleModal } from '@/components/EnhancementRuleModal'
import { EnhancementRule, EnhancementRuleSource, MatchType } from '@/types/EnhancementRule'

const duplicateData: Partial<EnhancementRule> = {
  patterns: [
    { id: 'p1', normalized_description: 'pocket eur savings eur', match_type: MatchType.EXACT, sort_order: 0 },
  ],
  source: EnhancementRuleSource.MANUAL,
}

const renderModal = (normalize?: (descriptions: string[]) => Promise<string[]>) => {
  const apiClient = createMockApiClient({
    categories: { getAll: vi.fn().mockResolvedValue({ categories: [], total: 0 }) },
    accounts: { getAll: vi.fn().mockResolvedValue([]) },
  })
  const create = vi.fn().mockImplementation((data) => Promise.resolve({ id: 'new-rule', ...data }))
  apiClient.enhancementRules.create = create
  apiClient.enhancementRules.previewMatchingTransactionsCount = vi.fn().mockResolvedValue({ count: 0, match_count: 0 })
  apiClient.enhancementRules.getMatchingTransactionsCount = vi.fn().mockResolvedValue({ count: 0, match_count: 0 })
  if (normalize) {
    apiClient.enhancementRules.normalizeDescriptions = vi.fn().mockImplementation(normalize)
  }

  const user = userEvent.setup()
  render(
    <ApiProvider client={apiClient}>
      <EnhancementRuleModal open duplicateData={duplicateData} onClose={vi.fn()} onSuccess={vi.fn()} />
    </ApiProvider>
  )
  return { create, user }
}

describe('EnhancementRuleModal duplicate + edit description', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => cleanup())

  test('changing the end of the description creates a rule with the edited description', async () => {
    const { create, user } = renderModal()

    const description = await screen.findByLabelText('Description')
    expect(description).toHaveValue('pocket eur savings eur')

    await user.clear(description)
    await user.type(description, 'pocket eur savings gbp')

    await user.click(screen.getByRole('button', { name: /create rule/i }))

    await waitFor(() => expect(create).toHaveBeenCalled())
    const payload = create.mock.calls[0][0]
    expect(payload.patterns[0].normalized_description).toBe('pocket eur savings gbp')
  })

  test('completely changing the description creates a rule with the new description', async () => {
    const { create, user } = renderModal()

    const description = await screen.findByLabelText('Description')
    await user.clear(description)
    await user.type(description, 'netflix monthly')

    await user.click(screen.getByRole('button', { name: /create rule/i }))

    await waitFor(() => expect(create).toHaveBeenCalled())
    const payload = create.mock.calls[0][0]
    expect(payload.patterns[0].normalized_description).toBe('netflix monthly')
  })

  test('shows how the typed description will be normalised (stripped chars are visible)', async () => {
    const { user } = renderModal(async (descriptions) =>
      descriptions.map((d) =>
        d
          .replace(/[^a-z\s]/gi, '')
          .replace(/\s+/g, ' ')
          .trim()
          .toLowerCase()
      )
    )

    const description = await screen.findByLabelText('Description')
    await user.clear(description)
    await user.type(description, 'pocket eur savings eur 2')

    expect(await screen.findByText('Will match: pocket eur savings eur')).toBeInTheDocument()
  })

  test('blocks creating a rule whose description normalises to nothing', async () => {
    const { create, user } = renderModal(async (descriptions) => descriptions.map(() => ''))

    const description = await screen.findByLabelText('Description')
    await user.clear(description)
    await user.type(description, '12345')

    expect(await screen.findByText(/no matchable text/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /create rule/i }))
    expect(create).not.toHaveBeenCalled()
  })
})
