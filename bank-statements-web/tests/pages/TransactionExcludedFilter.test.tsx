import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TransactionsPage } from '@/pages/Transactions'
import { ApiProvider } from '@/api/ApiContext'
import { createMockApiClient } from '../createMockApiClient'
import { Transaction, TransactionListResponse } from '@/types/Transaction'
import { Mock } from 'vitest'

vi.mock('@/api/FilterPresetClient', () => ({
  filterPresetClient: {
    getAll: vi.fn().mockResolvedValue([]),
    create: vi.fn().mockResolvedValue({ id: '1', name: 'test', filter_data: {}, created_at: '', updated_at: '' }),
    delete: vi.fn().mockResolvedValue(undefined),
  },
}))

const createTransaction = (overrides: Partial<Transaction> = {}): Transaction => ({
  id: '1',
  date: '2024-01-15',
  description: 'Test Transaction',
  normalized_description: 'test transaction',
  amount: -50.0,
  created_at: '2024-01-15T10:00:00Z',
  categorization_status: 'UNCATEGORIZED',
  exclude_from_analytics: false,
  ...overrides,
})

const createPaginatedResponse = (
  transactions: Transaction[],
  overrides: Partial<TransactionListResponse> = {}
): TransactionListResponse => ({
  transactions,
  total: transactions.length,
  page: 1,
  page_size: 20,
  total_pages: Math.ceil(transactions.length / 20) || 1,
  total_amount: transactions.reduce((sum, t) => sum + t.amount, 0),
  ...overrides,
})

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

interface RenderOptions {
  transactions?: TransactionListResponse
  categories?: { id: string; name: string }[]
  accounts?: { id: string; name: string }[]
  initialRoute?: string
  getAll?: Mock
  toggleExclude?: Mock
}

const renderTransactionsPage = (options: RenderOptions = {}) => {
  const {
    transactions = createPaginatedResponse([createTransaction()]),
    categories = [{ id: '1', name: 'Groceries' }],
    accounts = [{ id: '1', name: 'Current Account' }],
    initialRoute = '/transactions',
    getAll = vi.fn().mockResolvedValue(transactions),
    toggleExclude = vi.fn().mockResolvedValue({ ...createTransaction(), exclude_from_analytics: false }),
  } = options

  const apiClient = createMockApiClient({
    transactions: {
      getAll,
      toggleExcludeFromAnalytics: toggleExclude,
    },
    categories: {
      getAll: vi.fn().mockResolvedValue({ categories, total: categories.length }),
      getRootCategories: vi.fn().mockResolvedValue({ categories, total: categories.length }),
    },
    accounts: {
      getAll: vi.fn().mockResolvedValue(accounts),
    },
  })

  const user = userEvent.setup()
  const queryClient = createTestQueryClient()

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <ApiProvider client={apiClient}>
          <TransactionsPage />
        </ApiProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )

  return { apiClient, user, queryClient }
}

describe('Transaction Excluded Filter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('AC1: Filter for excluded transactions only', () => {
    test('displays excluded filter option in filter controls', async () => {
      renderTransactionsPage()

      await screen.findByText('Test Transaction')
      expect(
        screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      ).toBeInTheDocument()
    })

    test('calls API with exclude_from_analytics=true when excluded filter is applied', async () => {
      const getAll = vi
        .fn()
        .mockResolvedValueOnce(createPaginatedResponse([createTransaction()]))
        .mockResolvedValue(
          createPaginatedResponse([
            createTransaction({ id: '1', exclude_from_analytics: true, description: 'Excluded Transaction' }),
          ])
        )
      const { user } = renderTransactionsPage({ getAll })

      await screen.findByText('Test Transaction')

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBe(true)
      })
    })

    test('shows only excluded transactions when filter is active', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
        description: 'Excluded Purchase',
        exclude_from_analytics: true,
      })
      const getAll = vi
        .fn()
        .mockResolvedValueOnce(
          createPaginatedResponse([
            createTransaction({ id: '1', description: 'Regular Purchase' }),
            createTransaction({ id: '2', description: 'Excluded Purchase', exclude_from_analytics: true }),
          ])
        )
        .mockResolvedValueOnce(createPaginatedResponse([excludedTransaction]))

      const { user } = renderTransactionsPage({ getAll })

      await screen.findByText('Regular Purchase')

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        expect(screen.getByText('Excluded Purchase')).toBeInTheDocument()
      })
    })
  })

  describe('AC2: Re-include from filtered view', () => {
    test('re-including a transaction triggers list refresh', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
        description: 'Excluded Transaction',
        exclude_from_analytics: true,
      })
      const toggleExclude = vi.fn().mockResolvedValue({
        ...excludedTransaction,
        exclude_from_analytics: false,
      })
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([excludedTransaction]))

      const { user } = renderTransactionsPage({
        getAll,
        toggleExclude,
        initialRoute: '/transactions?exclude_from_analytics=true',
      })

      await screen.findByText('Excluded Transaction')

      const includeButton = screen.getByRole('button', { name: /include in analytics/i })
      await user.click(includeButton)

      await waitFor(() => {
        expect(toggleExclude).toHaveBeenCalledWith('1', false)
      })
    })

    test('re-included transaction calls toggle API with false', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
        description: 'Previously Excluded',
        exclude_from_analytics: true,
      })
      const toggleExclude = vi.fn().mockResolvedValue({
        ...excludedTransaction,
        exclude_from_analytics: false,
      })

      const { user } = renderTransactionsPage({
        transactions: createPaginatedResponse([excludedTransaction]),
        toggleExclude,
      })

      await screen.findByText('Previously Excluded')

      const includeButton = screen.getByRole('button', { name: /include in analytics/i })
      await user.click(includeButton)

      await waitFor(() => {
        expect(toggleExclude).toHaveBeenCalledWith('1', false)
      })
    })
  })

  describe('AC3: Clear excluded filter', () => {
    test('clearing excluded filter calls API without exclude_from_analytics', async () => {
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([createTransaction()]))

      const { user } = renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?exclude_from_analytics=true',
      })

      await screen.findByText('Test Transaction')

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBeUndefined()
      })
    })

    test('after clearing filter shows all transactions', async () => {
      const allTransactions = [
        createTransaction({ id: '1', description: 'Regular Purchase', exclude_from_analytics: false }),
        createTransaction({ id: '2', description: 'Excluded Purchase', exclude_from_analytics: true }),
      ]
      const getAll = vi
        .fn()
        .mockResolvedValueOnce(
          createPaginatedResponse([
            createTransaction({ id: '2', description: 'Excluded Purchase', exclude_from_analytics: true }),
          ])
        )
        .mockResolvedValueOnce(createPaginatedResponse(allTransactions))

      const { user } = renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?exclude_from_analytics=true',
      })

      await screen.findByText('Excluded Purchase')

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        expect(screen.getByText('Regular Purchase')).toBeInTheDocument()
        expect(screen.getByText('Excluded Purchase')).toBeInTheDocument()
      })
    })
  })

  describe('AC4: Excluded filter combines with other filters', () => {
    test('excluded filter preserves existing category filter in URL', async () => {
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([]))

      const { user } = renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?category_ids=1',
      })

      await waitFor(() => {
        expect(getAll).toHaveBeenCalled()
      })

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBe(true)
        expect(lastCall.category_ids).toContain('1')
      })
    })

    test('excluded filter preserves existing date range filter', async () => {
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([]))

      const { user } = renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?start_date=2024-01-01&end_date=2024-01-31',
      })

      await waitFor(() => {
        expect(getAll).toHaveBeenCalled()
      })

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBe(true)
        expect(lastCall.start_date).toBe('2024-01-01')
        expect(lastCall.end_date).toBe('2024-01-31')
      })
    })

    test('excluded filter preserves account filter', async () => {
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([]))

      const { user } = renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?account_id=1',
      })

      await waitFor(() => {
        expect(getAll).toHaveBeenCalled()
      })

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBe(true)
        expect(lastCall.account_id).toBe('1')
      })
    })
  })

  describe('URL persistence', () => {
    test('excluded filter is reflected in URL search params', async () => {
      const getAll = vi.fn().mockResolvedValue(createPaginatedResponse([createTransaction()]))
      const { user } = renderTransactionsPage({ getAll })

      await screen.findByText('Test Transaction')

      const excludedFilter = screen.getByRole('checkbox', { name: /excluded/i }) || screen.getByLabelText(/excluded/i)
      await user.click(excludedFilter)

      await waitFor(() => {
        const lastCall = getAll.mock.calls[getAll.mock.calls.length - 1][0]
        expect(lastCall.exclude_from_analytics).toBe(true)
      })
    })

    test('initialises excluded filter from URL search params', async () => {
      const getAll = vi
        .fn()
        .mockResolvedValue(createPaginatedResponse([createTransaction({ exclude_from_analytics: true })]))

      renderTransactionsPage({
        getAll,
        initialRoute: '/transactions?exclude_from_analytics=true',
      })

      await waitFor(() => {
        const firstCall = getAll.mock.calls[0]?.[0]
        expect(firstCall?.exclude_from_analytics).toBe(true)
      })
    })
  })
})
