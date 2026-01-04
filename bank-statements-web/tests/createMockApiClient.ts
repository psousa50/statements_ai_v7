import { ApiClient } from '@/api/ApiClient'
import { Account, AccountClient } from '@/api/AccountClient'
import { CategoryClient, CategoryListResponse } from '@/api/CategoryClient'
import { DescriptionGroupClient, DescriptionGroupListResponse } from '@/api/DescriptionGroupClient'
import { EnhancementRuleClient } from '@/api/EnhancementRuleClient'
import {
  StatementAnalysisResponse,
  StatementClient,
  StatementUploadResponse,
  StatementResponse,
  StatisticsPreviewResponse,
} from '@/api/StatementClient'
import {
  TransactionClient,
  CategoryTotalsResponse,
  CategoryTimeSeriesResponse,
  BulkUpdateTransactionsResponse,
  CountSimilarResponse,
  BulkReplaceCategoryResponse,
  EnhancementPreviewResponse,
  SavedFilterResponse,
} from '@/api/TransactionClient'
import { TransactionCategorizationClient } from '@/api/TransactionCategorizationClient'
import { Category, Transaction, TransactionListResponse } from '@/types/Transaction'
import {
  TransactionCategorization,
  TransactionCategorizationListResponse,
  TransactionCategorizationStats,
  CategorizationSource,
} from '@/types/TransactionCategorization'

// Default mock transaction
const defaultTransaction: Transaction = {
  id: '1',
  date: '2023-01-01',
  description: 'Sample Transaction',
  normalized_description: 'sample transaction',
  amount: 100,
  created_at: '2023-01-01T00:00:00Z',
  categorization_status: 'UNCATEGORIZED',
}

// Default mock category
const defaultCategory: Category = {
  id: '1',
  name: 'Sample Category',
}

// Default mock account
const defaultAccount: Account = {
  id: '1',
  name: 'Sample Account',
  currency: 'EUR',
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
      page: 1,
      page_size: 20,
      total_pages: 1,
    } as TransactionListResponse),
  exportCSV: () => Promise.resolve(),
  getCategoryTotals: () =>
    Promise.resolve({
      totals: [
        {
          category_id: '1',
          total_amount: 100,
          transaction_count: 1,
        },
        {
          category_id: undefined,
          total_amount: 50,
          transaction_count: 2,
        },
      ],
    } as CategoryTotalsResponse),
  getCategoryTimeSeries: () =>
    Promise.resolve({
      data_points: [],
    } as CategoryTimeSeriesResponse),
  getRecurringPatterns: () =>
    Promise.resolve({
      patterns: [],
      summary: {
        total_monthly_recurring: 0,
        pattern_count: 0,
      },
    }),
  getById: () => Promise.resolve(defaultTransaction),
  create: () => Promise.resolve(defaultTransaction),
  update: () => Promise.resolve(defaultTransaction),
  delete: () => Promise.resolve(),
  bulkUpdateCategory: () =>
    Promise.resolve({
      updated_count: 0,
      message: 'No transactions updated',
    } as BulkUpdateTransactionsResponse),
  countSimilar: () =>
    Promise.resolve({
      count: 0,
    } as CountSimilarResponse),
  countByCategory: () =>
    Promise.resolve({
      count: 0,
    } as CountSimilarResponse),
  bulkReplaceCategory: () =>
    Promise.resolve({
      updated_count: 0,
      message: 'No transactions updated',
    } as BulkReplaceCategoryResponse),
  categorize: function (_id: string, _categoryId?: string): Promise<Transaction> {
    throw new Error('Function not implemented.')
  },
  previewEnhancement: () =>
    Promise.resolve({
      matched: false,
    } as EnhancementPreviewResponse),
  createSavedFilter: (transactionIds: string[]) =>
    Promise.resolve({
      id: 'mock-saved-filter-id',
      transaction_ids: transactionIds,
    } as SavedFilterResponse),
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
  generateSuggestions: () =>
    Promise.resolve({
      suggestions: [],
      total_descriptions_analysed: 0,
    }),
  createSelectedCategories: () =>
    Promise.resolve({
      categories_created: 0,
      categories: [],
    }),
  exportCategories: () => Promise.resolve(),
  uploadCategories: () =>
    Promise.resolve({
      categories_created: 0,
      categories_found: 0,
      total_processed: 0,
      categories: [],
    }),
}

// Default mock account client implementation
const defaultAccountClient: AccountClient = {
  getAll: () => Promise.resolve([defaultAccount]),
  getById: () => Promise.resolve(defaultAccount),
  createAccount: () => Promise.resolve(defaultAccount),
  updateAccount: () => Promise.resolve(defaultAccount),
  deleteAccount: () => Promise.resolve(),
  setInitialBalance: () => Promise.resolve(defaultAccount),
  deleteInitialBalance: () => Promise.resolve(),
  exportAccounts: () => Promise.resolve(),
  uploadAccounts: () => Promise.resolve({ accounts: [], total: 0, created: 0, updated: 0 }),
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
      dropped_rows: [],
      dropped_rows_count: 0,
    } as StatementAnalysisResponse),
  uploadStatement: (request) =>
    Promise.resolve({
      uploaded_file_id: request.uploaded_file_id,
      transactions_saved: 10,
      duplicated_transactions: 0,
      success: true,
      message: 'Successfully saved 10 transactions',
      total_processed: 10,
      rule_based_matches: 5,
      match_rate_percentage: 50,
      processing_time_ms: 100,
    } as StatementUploadResponse),
  previewStatistics: () =>
    Promise.resolve({
      total_transactions: 2,
      unique_transactions: 2,
      duplicate_transactions: 0,
      date_range: ['2023-01-01', '2023-01-02'],
      total_amount: 300,
      total_debit: 0,
      total_credit: 300,
    } as StatisticsPreviewResponse),
  listStatements: () => Promise.resolve([] as StatementResponse[]),
  deleteStatement: () => Promise.resolve({ message: 'Statement deleted successfully' }),
}

// Default mock enhancement rule client implementation
const defaultEnhancementRuleClient: EnhancementRuleClient = {
  getAll: () => Promise.resolve({ rules: [], total: 0 }),
  getStats: () =>
    Promise.resolve({
      summary: {
        total_rules: 0,
        manual_rules: 0,
        auto_rules: 0,
        category_only_rules: 0,
        counterparty_only_rules: 0,
        combined_rules: 0,
        total_transactions_enhanced: 0,
        transactions_with_manual_rules: 0,
        transactions_with_auto_rules: 0,
      },
      rule_type_usage: [],
      category_usage: [],
      counterparty_usage: [],
      top_rules_by_usage: [],
      unused_rules: [],
    }),
  getById: () => Promise.reject(new Error('Not implemented')),
  getMatchingTransactionsCount: () => Promise.resolve({ count: 0 }),
  previewMatchingTransactionsCount: () => Promise.resolve({ count: 0 }),
  create: () => Promise.reject(new Error('Not implemented')),
  update: () => Promise.reject(new Error('Not implemented')),
  delete: () => Promise.resolve(),
  cleanupUnused: () => Promise.resolve({ deleted_count: 0, message: 'No unused rules found' }),
  suggestCategories: () => Promise.resolve({ processed: 0, auto_applied: 0, suggestions: 0, failed: 0 }),
  suggestCounterparties: () => Promise.resolve({ processed: 0, auto_applied: 0, suggestions: 0, failed: 0 }),
  applySuggestion: () => Promise.resolve({ rule_id: '', applied: true, transactions_updated: 0 }),
  rejectSuggestion: () => Promise.resolve({ rule_id: '', applied: false, transactions_updated: 0 }),
}

const defaultDescriptionGroupClient: DescriptionGroupClient = {
  getAll: () => Promise.resolve({ groups: [], total: 0 } as DescriptionGroupListResponse),
  getById: () => Promise.reject(new Error('Not implemented')),
  create: () => Promise.reject(new Error('Not implemented')),
  update: () => Promise.reject(new Error('Not implemented')),
  delete: () => Promise.resolve(),
}

type TransactionClientOverrides = Partial<{
  [K in keyof TransactionClient]: TransactionClient[K]
}>
type CategoryClientOverrides = Partial<{
  [K in keyof CategoryClient]: CategoryClient[K]
}>
type AccountClientOverrides = Partial<{
  [K in keyof AccountClient]: AccountClient[K]
}>
type StatementClientOverrides = Partial<{
  [K in keyof StatementClient]: StatementClient[K]
}>
type TransactionCategorizationClientOverrides = Partial<{
  [K in keyof TransactionCategorizationClient]: TransactionCategorizationClient[K]
}>

// Type for partial overrides of the API client
interface ApiClientOverrides {
  transactions?: TransactionClientOverrides
  transactionCategorizations?: TransactionCategorizationClientOverrides
  categories?: CategoryClientOverrides
  accounts?: AccountClientOverrides
  statements?: StatementClientOverrides
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
    accounts: {
      ...defaultAccountClient,
      ...overrides.accounts,
    },
    statements: {
      ...defaultStatementClient,
      ...overrides.statements,
    },
    enhancementRules: defaultEnhancementRuleClient,
    descriptionGroups: defaultDescriptionGroupClient,
  }
}
