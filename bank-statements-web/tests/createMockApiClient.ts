import { ApiClient } from '@/api/ApiClient'
import { CategoryClient, CategoryListResponse } from '@/api/CategoryClient'
import { Source, SourceClient } from '@/api/SourceClient'
import { StatementAnalysisResponse, StatementClient, StatementUploadResponse } from '@/api/StatementClient'
import { TransactionClient, CategoryTotalsResponse, BulkUpdateTransactionsResponse } from '@/api/TransactionClient'
import { TransactionCategorizationClient } from '@/api/TransactionCategorizationClient'
import { Category, Transaction, TransactionListResponse } from '@/types/Transaction'
import { 
  TransactionCategorization, 
  TransactionCategorizationListResponse,
  TransactionCategorizationStats,
  CategorizationSource
} from '@/types/TransactionCategorization'

// Default mock transaction
const defaultTransaction: Transaction = {
  id: '1',
  date: '2023-01-01',
  description: 'Sample Transaction',
  amount: 100,
  created_at: '2023-01-01T00:00:00Z',
  categorization_status: 'UNCATEGORIZED',
}

// Default mock category
const defaultCategory: Category = {
  id: '1',
  name: 'Sample Category',
}

// Default mock source
const defaultSource: Source = {
  id: '1',
  name: 'Sample Bank',
}

// Default mock transaction categorization
const defaultTransactionCategorization: TransactionCategorization = {
  id: '1',
  normalized_description: 'walmart',
  category_id: '1',
  source: CategorizationSource.AI,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  category: defaultCategory,
  transaction_count: 5,
}

// Default mock transaction client implementation
const defaultTransactionClient: TransactionClient = {
  getAll: () =>
    Promise.resolve({
      transactions: [defaultTransaction],
      total: 1,
    } as TransactionListResponse),
  getCategoryTotals: () =>
    Promise.resolve({
      totals: [
        {
          category_id: '1',
          total_amount: 100,
          transaction_count: 1,
        },
        {
          category_id: undefined, // uncategorized
          total_amount: 50,
          transaction_count: 2,
        },
      ],
    } as CategoryTotalsResponse),
  getById: () => Promise.resolve(defaultTransaction),
  create: () => Promise.resolve(defaultTransaction),
  update: () => Promise.resolve(defaultTransaction),
  delete: () => Promise.resolve(),
  bulkUpdateCategory: () => Promise.resolve({
    updated_count: 0,
    message: 'No transactions updated'
  } as BulkUpdateTransactionsResponse),
}

// Default mock category client implementation
const defaultCategoryClient: CategoryClient = {
  getAll: () =>
    Promise.resolve({
      categories: [defaultCategory],
      total: 1,
    } as CategoryListResponse),
  getRootCategories: () =>
    Promise.resolve({
      categories: [defaultCategory],
      total: 1,
    } as CategoryListResponse),
  getById: () => Promise.resolve(defaultCategory),
  getSubcategories: () =>
    Promise.resolve({
      categories: [],
      total: 0,
    } as CategoryListResponse),
  create: () => Promise.resolve(defaultCategory),
  update: () => Promise.resolve(defaultCategory),
  delete: () => Promise.resolve(),
}

// Default mock source client implementation
const defaultSourceClient: SourceClient = {
  getAll: () => Promise.resolve([defaultSource]),
  createSource: () => Promise.resolve(defaultSource),
}

// Default mock transaction categorization client implementation
const defaultTransactionCategorizationClient: TransactionCategorizationClient = {
  getAll: () =>
    Promise.resolve({
      categorizations: [defaultTransactionCategorization],
      total: 1,
    } as TransactionCategorizationListResponse),
  getStats: () =>
    Promise.resolve({
      summary: {
        total_rules: 1,
        manual_rules: 0,
        ai_rules: 1,
        total_transactions_categorized: 5,
        transactions_with_manual_rules: 0,
        transactions_with_ai_rules: 5,
      },
      category_usage: [],
      top_rules_by_usage: [],
      unused_rules: [],
    } as TransactionCategorizationStats),
  getById: () => Promise.resolve(defaultTransactionCategorization),
  create: () => Promise.resolve(defaultTransactionCategorization),
  update: () => Promise.resolve(defaultTransactionCategorization),
  delete: () => Promise.resolve(),
  cleanupUnused: () => Promise.resolve({ deleted_count: 0, message: 'No unused rules found' }),
}

// Default mock statement client implementation
const defaultStatementClient: StatementClient = {
  analyzeStatement: () =>
    Promise.resolve({
      uploaded_file_id: '1',
      file_type: 'CSV',
      column_mapping: {
        date: 'Date',
        amount: 'Amount',
        description: 'Description',
      },
      header_row_index: 0,
      data_start_row_index: 1,
      sample_data: [
        ['Date', 'Amount', 'Description'],
        ['2023-01-01', '100', 'Sample Transaction'],
        ['2023-01-02', '200', 'Another Transaction'],
      ],
      total_transactions: 2,
      unique_transactions: 2,
      duplicate_transactions: 0,
      date_range: ['2023-01-01', '2023-01-02'],
      total_amount: 300,
      total_debit: 0,
      total_credit: 300,
    } as StatementAnalysisResponse),
  uploadStatement: (request) =>
    Promise.resolve({
      uploaded_file_id: request.uploaded_file_id,
      transactions_saved: 10,
      success: true,
      message: 'Successfully saved 10 transactions',
    } as StatementUploadResponse),
}

type TransactionClientOverrides = Partial<{
  [K in keyof TransactionClient]: TransactionClient[K]
}>
type CategoryClientOverrides = Partial<{
  [K in keyof CategoryClient]: CategoryClient[K]
}>
type StatementClientOverrides = Partial<{
  [K in keyof StatementClient]: StatementClient[K]
}>
type SourceClientOverrides = Partial<{
  [K in keyof SourceClient]: SourceClient[K]
}>
type TransactionCategorizationClientOverrides = Partial<{
  [K in keyof TransactionCategorizationClient]: TransactionCategorizationClient[K]
}>

// Type for partial overrides of the API client
interface ApiClientOverrides {
  transactions?: TransactionClientOverrides
  transactionCategorizations?: TransactionCategorizationClientOverrides
  categories?: CategoryClientOverrides
  statements?: StatementClientOverrides
  sources?: SourceClientOverrides
}

// Create a mock API client with optional overrides
export const createMockApiClient = (overrides: ApiClientOverrides = {}): ApiClient => {
  return {
    transactions: {
      ...defaultTransactionClient,
      ...overrides.transactions,
    },
    transactionCategorizations: {
      ...defaultTransactionCategorizationClient,
      ...overrides.transactionCategorizations,
    },
    categories: {
      ...defaultCategoryClient,
      ...overrides.categories,
    },
    statements: {
      ...defaultStatementClient,
      ...overrides.statements,
    },
    sources: {
      ...defaultSourceClient,
      ...overrides.sources,
    },
  }
}
