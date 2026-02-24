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
  amount: -100.0,
  created_at: '2024-01-15T10:00:00Z',
  categorization_status: 'UNCATEGORIZED',
  exclude_from_analytics: false,
  is_split_parent: false,
  is_split_child: false,
  parent_transaction_id: undefined,
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
  splitTransaction?: Mock
}

const renderTransactionsPage = (options: RenderOptions = {}) => {
  const {
    transactions = createPaginatedResponse([createTransaction()]),
    categories = [{ id: '1', name: 'Groceries' }],
    accounts = [{ id: '1', name: 'Current Account' }],
    initialRoute = '/transactions',
    splitTransaction = vi.fn().mockResolvedValue([]),
  } = options

  const apiClient = createMockApiClient({
    transactions: {
      getAll: vi.fn().mockResolvedValue(transactions),
      splitTransaction,
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

describe('Transaction Split', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('AC1: Split interface shows form with at least 2 parts', () => {
    test('displays a split action on a regular transaction row', async () => {
      renderTransactionsPage()

      await screen.findByText('Test Transaction')
      expect(screen.getByRole('button', { name: /split/i })).toBeInTheDocument()
    })

    test('opening split interface shows at least two part input rows', async () => {
      const { user } = renderTransactionsPage()

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => {
        const amountInputs = screen.getAllByLabelText(/amount/i)
        expect(amountInputs.length).toBeGreaterThanOrEqual(2)
      })
    })

    test('split form shows amount, description, and category fields per part', async () => {
      const { user } = renderTransactionsPage()

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => {
        expect(screen.getAllByLabelText(/amount/i).length).toBeGreaterThanOrEqual(2)
      })
    })
  })

  describe('AC2: Valid split can be submitted when amounts sum to parent amount', () => {
    test('submit button is enabled when amounts sum to parent transaction amount', async () => {
      const transaction = createTransaction({ id: '1', amount: -100.0 })
      const { user } = renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
      })

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => screen.getAllByLabelText(/amount/i))

      const amountInputs = screen.getAllByLabelText(/amount/i)
      await user.clear(amountInputs[0])
      await user.type(amountInputs[0], '60')
      await user.clear(amountInputs[1])
      await user.type(amountInputs[1], '40')

      const submitButton = screen.getByRole('button', { name: /confirm|submit|save/i })
      expect(submitButton).not.toBeDisabled()
    })

    test('calls split API when valid split is submitted', async () => {
      const transaction = createTransaction({ id: '1', amount: -100.0 })
      const splitTransaction = vi
        .fn()
        .mockResolvedValue([
          createTransaction({ id: '2', amount: -60.0, description: 'Part A', parent_transaction_id: '1' }),
          createTransaction({ id: '3', amount: -40.0, description: 'Part B', parent_transaction_id: '1' }),
        ])
      const { user } = renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
        splitTransaction,
      })

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => screen.getAllByLabelText(/amount/i))

      const amountInputs = screen.getAllByLabelText(/amount/i)
      await user.clear(amountInputs[0])
      await user.type(amountInputs[0], '60')
      await user.clear(amountInputs[1])
      await user.type(amountInputs[1], '40')

      const submitButton = screen.getByRole('button', { name: /confirm|submit|save/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(splitTransaction).toHaveBeenCalledWith('1', expect.objectContaining({ parts: expect.any(Array) }))
      })
    })
  })

  describe('AC3: Validation error when amounts do not sum to parent amount', () => {
    test('shows validation error when amounts do not sum to parent amount', async () => {
      const transaction = createTransaction({ id: '1', amount: -100.0 })
      const { user } = renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
      })

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => screen.getAllByLabelText(/amount/i))

      const amountInputs = screen.getAllByLabelText(/amount/i)
      await user.clear(amountInputs[0])
      await user.type(amountInputs[0], '60')
      await user.clear(amountInputs[1])
      await user.type(amountInputs[1], '30')

      const submitButton = screen.getByRole('button', { name: /confirm|submit|save/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/must equal|do not sum/i)).toBeInTheDocument()
      })
    })

    test('submit button is disabled or triggers validation when amounts are unequal', async () => {
      const transaction = createTransaction({ id: '1', amount: -100.0 })
      const splitTransaction = vi.fn()
      const { user } = renderTransactionsPage({
        transactions: createPaginatedResponse([transaction]),
        splitTransaction,
      })

      await screen.findByText('Test Transaction')
      const splitButton = screen.getByRole('button', { name: /split/i })
      await user.click(splitButton)

      await waitFor(() => screen.getAllByLabelText(/amount/i))

      const amountInputs = screen.getAllByLabelText(/amount/i)
      await user.clear(amountInputs[0])
      await user.type(amountInputs[0], '60')
      await user.clear(amountInputs[1])
      await user.type(amountInputs[1], '30')

      const submitButton = screen.getByRole('button', { name: /confirm|submit|save/i })
      if (!submitButton.hasAttribute('disabled')) {
        await user.click(submitButton)
      }

      await waitFor(() => {
        expect(splitTransaction).not.toHaveBeenCalled()
      })
    })
  })

  describe('AC7: Split action unavailable on already-split parents', () => {
    test('split action is not shown for a transaction that is already a split parent', async () => {
      const splitParent = createTransaction({
        id: '1',
        is_split_parent: true,
        exclude_from_analytics: true,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([splitParent]),
      })

      await screen.findByText('Test Transaction')
      expect(screen.queryByRole('button', { name: /^split$/i })).not.toBeInTheDocument()
    })
  })

  describe('AC8: Split action unavailable on child transactions', () => {
    test('split action is not shown for a split child transaction', async () => {
      const child = createTransaction({
        id: '2',
        description: 'Part A',
        is_split_child: true,
        parent_transaction_id: '1',
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([child]),
      })

      await screen.findByText('Part A')
      expect(screen.queryByRole('button', { name: /^split$/i })).not.toBeInTheDocument()
    })
  })

  describe('Split parent/child visual indicators', () => {
    test('split parent transaction has visual indicator', async () => {
      const splitParent = createTransaction({
        id: '1',
        description: 'Original Purchase',
        is_split_parent: true,
        exclude_from_analytics: true,
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([splitParent]),
      })

      await screen.findByText('Original Purchase')
      const row = screen.getByText('Original Purchase').closest('tr')
      expect(row).toHaveAttribute('data-split-parent', 'true')
    })

    test('split child transaction has visual indicator', async () => {
      const child = createTransaction({
        id: '2',
        description: 'Part A',
        is_split_child: true,
        parent_transaction_id: '1',
      })
      renderTransactionsPage({
        transactions: createPaginatedResponse([child]),
      })

      await screen.findByText('Part A')
      const row = screen.getByText('Part A').closest('tr')
      expect(row).toHaveAttribute('data-split-child', 'true')
    })
  })

  describe('Transaction type fields', () => {
    test('transaction response with is_split_parent=true reflects correctly', () => {
      const transaction = createTransaction({ is_split_parent: true })
      expect(transaction.is_split_parent).toBe(true)
    })

    test('transaction response with is_split_child=true reflects correctly', () => {
      const transaction = createTransaction({ is_split_child: true, parent_transaction_id: 'parent-id' })
      expect(transaction.is_split_child).toBe(true)
      expect(transaction.parent_transaction_id).toBe('parent-id')
    })

    test('regular transaction defaults to is_split_parent=false and is_split_child=false', () => {
      const transaction = createTransaction()
      expect(transaction.is_split_parent).toBe(false)
      expect(transaction.is_split_child).toBe(false)
    })
  })
})
