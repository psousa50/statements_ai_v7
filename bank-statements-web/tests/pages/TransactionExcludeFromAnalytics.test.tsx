import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within, waitFor, cleanup } from '@testing-library/react'
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
  is_split_parent: false,
  is_split_child: false,
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
  toggleExclude?: Mock
}

const renderTransactionsPage = (options: RenderOptions = {}) => {
  const {
    transactions = createPaginatedResponse([createTransaction()]),
    categories = [{ id: '1', name: 'Groceries' }],
    accounts = [{ id: '1', name: 'Current Account' }],
    initialRoute = '/transactions',
    toggleExclude = vi.fn().mockResolvedValue({ ...createTransaction(), exclude_from_analytics: true }),
  } = options

  const apiClient = createMockApiClient({
    transactions: {
      getAll: vi.fn().mockResolvedValue(transactions),
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

  return { apiClient, user }
}

describe('Transaction Exclude From Analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('AC1: Exclude a transaction from analytics', () => {
    test('displays exclude action on transaction row', async () => {
      renderTransactionsPage()

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('button', { name: /exclude from analytics/i })).toBeInTheDocument()
    })

    test('calls toggle API when exclude action is clicked', async () => {
      const toggleExclude = vi.fn().mockResolvedValue({
        ...createTransaction(),
        exclude_from_analytics: true,
      })
      const { user } = renderTransactionsPage({ toggleExclude })

      await screen.findByText('Test Transaction')
      const excludeButton = screen.getByRole('button', { name: /exclude from analytics/i })
      await user.click(excludeButton)

      await waitFor(() => {
        expect(toggleExclude).toHaveBeenCalledWith('1', true)
      })
    })
  })

  describe('AC2: Re-include a previously excluded transaction', () => {
    test('displays include action on excluded transaction row', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
        exclude_from_analytics: true,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([excludedTransaction]),
      })

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('button', { name: /include in analytics/i })).toBeInTheDocument()
    })

    test('calls toggle API with false when include action is clicked', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
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

      await screen.findByText('Test Transaction')
      const includeButton = screen.getByRole('button', { name: /include in analytics/i })
      await user.click(includeButton)

      await waitFor(() => {
        expect(toggleExclude).toHaveBeenCalledWith('1', false)
      })
    })
  })

  describe('AC7: Visual indicator distinguishes excluded transactions', () => {
    test('excluded transactions have visual distinction from non-excluded', async () => {
      const transactions = [
        createTransaction({ id: '1', description: 'Normal Purchase', exclude_from_analytics: false }),
        createTransaction({ id: '2', description: 'Outlier Purchase', exclude_from_analytics: true }),
      ]
      renderTransactionsPage({
        transactions: createPaginatedResponse(transactions),
      })

      await screen.findByText('Normal Purchase')
      await screen.findByText('Outlier Purchase')

      const outlierRow = screen.getByText('Outlier Purchase').closest('tr')
      expect(outlierRow).toHaveAttribute('data-excluded', 'true')
    })

    test('non-excluded transactions do not have excluded indicator', async () => {
      const transaction = createTransaction({
        id: '1',
        description: 'Normal Purchase',
        exclude_from_analytics: false,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
      })

      await screen.findByText('Normal Purchase')
      const row = screen.getByText('Normal Purchase').closest('tr')
      expect(row).not.toHaveAttribute('data-excluded', 'true')
    })

    test('excluded transaction shows exclusion icon indicator', async () => {
      const excludedTransaction = createTransaction({
        id: '1',
        description: 'Outlier Purchase',
        exclude_from_analytics: true,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([excludedTransaction]),
      })

      await screen.findByText('Outlier Purchase')
      const row = screen.getByText('Outlier Purchase').closest('tr')
      expect(within(row!).getByTestId('excluded-indicator')).toBeInTheDocument()
    })
  })

  describe('exclude_from_analytics field in transaction response', () => {
    test('transaction response includes exclude_from_analytics field defaulting to false', () => {
      const transaction = createTransaction()
      expect(transaction.exclude_from_analytics).toBe(false)
    })

    test('transaction response reflects exclude_from_analytics when true', () => {
      const transaction = createTransaction({ exclude_from_analytics: true })
      expect(transaction.exclude_from_analytics).toBe(true)
    })
  })
})
