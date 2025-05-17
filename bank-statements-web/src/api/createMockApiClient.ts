import { ApiClient } from './ApiClient'
import { CategoryClient, CategoryListResponse } from './CategoryClient'
import { Source, SourceClient, SourceListResponse } from './SourceClient'
import { SampleData, StatementAnalysisResponse, StatementClient, StatementUploadResponse } from './StatementClient'
import { TransactionClient } from './TransactionClient'
import { Category, Transaction, TransactionListResponse } from '../types/Transaction'

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

// Default mock transaction client implementation
const defaultTransactionClient: TransactionClient = {
  getAll: () =>
    Promise.resolve({
      transactions: [defaultTransaction],
      total: 1,
    } as TransactionListResponse),
  getById: () => Promise.resolve(defaultTransaction),
  create: () => Promise.resolve(defaultTransaction),
  update: () => Promise.resolve(defaultTransaction),
  delete: () => Promise.resolve(),
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
  getSources: () =>
    Promise.resolve({
      sources: [defaultSource],
      total: 1,
    } as SourceListResponse),
  createSource: () => Promise.resolve(defaultSource),
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
        ["Date", "Amount", "Description"],
        ["2023-01-01", "100", "Sample Transaction"],
        ["2023-01-02", "200", "Another Transaction"]
      ]
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

// Type for partial overrides of the API client
interface ApiClientOverrides {
  transactions?: TransactionClientOverrides
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
