import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { TransactionsPage } from '@/pages/Transactions'
import { ApiProvider } from '@/api/ApiContext'
import { createMockApiClient } from '../createMockApiClient'
import { Transaction, TransactionListResponse } from '@/types/Transaction'
import { Mock } from 'vitest'

const createTransaction = (overrides: Partial<Transaction> = {}): Transaction => ({
  id: '1',
  date: '2024-01-15',
  description: 'Test Transaction',
  normalized_description: 'test transaction',
  amount: -50.0,
  created_at: '2024-01-15T10:00:00Z',
  categorization_status: 'UNCATEGORIZED',
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

interface RenderOptions {
  transactions?: TransactionListResponse
  categories?: { id: string; name: string }[]
  accounts?: { id: string; name: string }[]
  initialRoute?: string
}

const renderTransactionsPage = (options: RenderOptions = {}) => {
  const {
    transactions = createPaginatedResponse([createTransaction()]),
    categories = [{ id: '1', name: 'Groceries' }],
    accounts = [{ id: '1', name: 'Current Account' }],
    initialRoute = '/transactions',
  } = options

  const apiClient = createMockApiClient({
    transactions: {
      getAll: vi.fn().mockResolvedValue(transactions),
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

  render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <ApiProvider client={apiClient}>
        <TransactionsPage />
      </ApiProvider>
    </MemoryRouter>
  )

  return { apiClient, user }
}

describe('TransactionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('rendering', () => {
    test('renders page heading and description', async () => {
      renderTransactionsPage()

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('heading', { name: 'Transactions', level: 1 })).toBeInTheDocument()
      expect(screen.getByText(/view and manage your bank transactions/i)).toBeInTheDocument()
    })

    test('renders action buttons in header', async () => {
      renderTransactionsPage()

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('button', { name: /download csv/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /new transaction/i })).toBeInTheDocument()
    })

    test('displays transaction in the list', async () => {
      const transaction = createTransaction({
        description: 'Coffee Shop Purchase',
        amount: -4.5,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
      })

      expect(await screen.findByText('Coffee Shop Purchase')).toBeInTheDocument()
    })

    test('displays multiple transactions', async () => {
      const transactions = [
        createTransaction({ id: '1', description: 'Coffee Shop', amount: -4.5 }),
        createTransaction({ id: '2', description: 'Salary', amount: 3000 }),
        createTransaction({ id: '3', description: 'Rent Payment', amount: -1200 }),
      ]
      renderTransactionsPage({
        transactions: createPaginatedResponse(transactions),
      })

      expect(await screen.findByText('Coffee Shop')).toBeInTheDocument()
      expect(screen.getByText('Salary')).toBeInTheDocument()
      expect(screen.getByText('Rent Payment')).toBeInTheDocument()
    })

    test('shows transaction count in summary', async () => {
      const transactions = [
        createTransaction({ id: '1' }),
        createTransaction({ id: '2' }),
        createTransaction({ id: '3' }),
      ]
      renderTransactionsPage({
        transactions: createPaginatedResponse(transactions),
      })

      expect(await screen.findByText('3 transactions found')).toBeInTheDocument()
    })

    test('shows total amount in summary', async () => {
      const transactions = [
        createTransaction({ id: '1', amount: -100 }),
        createTransaction({ id: '2', amount: 50 }),
      ]
      renderTransactionsPage({
        transactions: createPaginatedResponse(transactions, { total_amount: -50 }),
      })

      await screen.findByText('2 transactions found')
      expect(screen.getByText(/total:/i)).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    test('handles empty transaction list', async () => {
      renderTransactionsPage({
        transactions: createPaginatedResponse([]),
      })

      await waitFor(() => {
        expect(screen.queryByText(/transactions found/)).not.toBeInTheDocument()
      })
    })
  })

  describe('loading state', () => {
    test('renders page while data is loading', async () => {
      let resolvePromise: (value: TransactionListResponse) => void
      const pendingPromise = new Promise<TransactionListResponse>((resolve) => {
        resolvePromise = resolve
      })

      const apiClient = createMockApiClient({
        transactions: {
          getAll: vi.fn().mockReturnValue(pendingPromise),
        },
      })

      render(
        <MemoryRouter>
          <ApiProvider client={apiClient}>
            <TransactionsPage />
          </ApiProvider>
        </MemoryRouter>
      )

      expect(screen.getByRole('heading', { name: 'Transactions', level: 1 })).toBeInTheDocument()

      resolvePromise!(createPaginatedResponse([]))
      await waitFor(() => {
        expect(screen.queryByText('Loading')).not.toBeInTheDocument()
      })
    })
  })

  describe('error state', () => {
    test('displays error message when API fails', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const apiClient = createMockApiClient({
        transactions: {
          getAll: vi.fn().mockRejectedValue(new Error('Network error')),
        },
      })

      render(
        <MemoryRouter>
          <ApiProvider client={apiClient}>
            <TransactionsPage />
          </ApiProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      consoleSpy.mockRestore()
    })
  })

  describe('sorting', () => {
    test('calls API with sort parameters when clicking column header', async () => {
      const { apiClient, user } = renderTransactionsPage()

      await screen.findByText('Test Transaction')

      const table = screen.getByRole('table')
      const descriptionHeader = within(table).getByText('Description')
      await user.click(descriptionHeader)

      await waitFor(() => {
        const mockGetAll = apiClient.transactions.getAll as Mock
        const lastCall = mockGetAll.mock.calls[mockGetAll.mock.calls.length - 1][0]
        expect(lastCall.sort_field).toBe('description')
      })
    })

    test('toggles sort direction when clicking same column', async () => {
      const { apiClient, user } = renderTransactionsPage()

      await screen.findByText('Test Transaction')

      const mockGetAll = apiClient.transactions.getAll as Mock
      const initialCallCount = mockGetAll.mock.calls.length

      const table = screen.getByRole('table')
      const dateHeader = within(table).getByText('Date')
      await user.click(dateHeader)

      await waitFor(() => {
        expect(mockGetAll.mock.calls.length).toBeGreaterThan(initialCallCount)
        const lastCall = mockGetAll.mock.calls[mockGetAll.mock.calls.length - 1][0]
        expect(lastCall.sort_field).toBe('date')
        expect(lastCall.sort_direction).toBe('asc')
      })
    })
  })

  describe('pagination', () => {
    test('shows pagination when there are multiple pages', async () => {
      renderTransactionsPage({
        transactions: createPaginatedResponse(
          [createTransaction()],
          { total: 50, total_pages: 3, page_size: 20 }
        ),
      })

      await screen.findByText('Test Transaction')
      expect(screen.getByText(/showing 1-20 of 50/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument()
    })

    test('calls API with new page when navigating', async () => {
      const { apiClient, user } = renderTransactionsPage({
        transactions: createPaginatedResponse(
          [createTransaction()],
          { total: 50, total_pages: 3, page_size: 20 }
        ),
      })

      await screen.findByText('Test Transaction')

      const page2Button = screen.getByRole('button', { name: '2' })
      await user.click(page2Button)

      await waitFor(() => {
        const mockGetAll = apiClient.transactions.getAll as Mock
        const lastCall = mockGetAll.mock.calls[mockGetAll.mock.calls.length - 1][0]
        expect(lastCall.page).toBe(2)
      })
    })
  })

  describe('new transaction modal', () => {
    test('opens modal when clicking New Transaction button', async () => {
      const { user } = renderTransactionsPage()

      await screen.findByText('Test Transaction')

      const newButton = screen.getByRole('button', { name: /new transaction/i })
      await user.click(newButton)

      expect(await screen.findByRole('heading', { name: /add new transaction/i })).toBeInTheDocument()
    })
  })

  describe('CSV export', () => {
    test('disables export button when no transactions', async () => {
      renderTransactionsPage({
        transactions: createPaginatedResponse([]),
      })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /download csv/i })).toBeDisabled()
      })
    })

    test('enables export button when transactions exist', async () => {
      renderTransactionsPage({
        transactions: createPaginatedResponse([createTransaction()]),
      })

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('button', { name: /download csv/i })).not.toBeDisabled()
    })
  })
})

describe('convertAmountFiltersForApi', () => {
  const convertAmountFiltersForApi = (
    minAmount: number | undefined,
    maxAmount: number | undefined,
    transactionType: 'all' | 'debit' | 'credit'
  ): { min_amount?: number; max_amount?: number } => {
    if (minAmount === undefined && maxAmount === undefined) {
      return {}
    }

    const bothPositive = (minAmount === undefined || minAmount >= 0) && (maxAmount === undefined || maxAmount >= 0)

    if (transactionType === 'debit' && bothPositive) {
      return {
        min_amount: maxAmount !== undefined ? -maxAmount : undefined,
        max_amount: minAmount !== undefined ? -minAmount : undefined,
      }
    }

    return { min_amount: minAmount, max_amount: maxAmount }
  }

  test('returns empty object when both amounts undefined', () => {
    expect(convertAmountFiltersForApi(undefined, undefined, 'all')).toEqual({})
  })

  test('returns amounts as-is for "all" transaction type', () => {
    expect(convertAmountFiltersForApi(10, 100, 'all')).toEqual({ min_amount: 10, max_amount: 100 })
  })

  test('returns amounts as-is for "credit" transaction type', () => {
    expect(convertAmountFiltersForApi(10, 100, 'credit')).toEqual({ min_amount: 10, max_amount: 100 })
  })

  test('inverts and negates amounts for "debit" with positive values', () => {
    expect(convertAmountFiltersForApi(10, 100, 'debit')).toEqual({ min_amount: -100, max_amount: -10 })
  })

  test('handles only min amount for debit', () => {
    expect(convertAmountFiltersForApi(50, undefined, 'debit')).toEqual({ min_amount: undefined, max_amount: -50 })
  })

  test('handles only max amount for debit', () => {
    expect(convertAmountFiltersForApi(undefined, 200, 'debit')).toEqual({ min_amount: -200, max_amount: undefined })
  })

  test('does not invert for debit when values are already negative', () => {
    expect(convertAmountFiltersForApi(-100, -10, 'debit')).toEqual({ min_amount: -100, max_amount: -10 })
  })
})
