import { ApiClient } from './ApiClient';
import { CategoryClient, CategoryListResponse } from './CategoryClient';
import { TransactionClient } from './TransactionClient';
import { Category, Transaction, TransactionListResponse } from '../types/Transaction';

// Default mock transaction
const defaultTransaction: Transaction = {
  id: '1',
  date: '2023-01-01',
  description: 'Sample Transaction',
  amount: 100,
  created_at: '2023-01-01T00:00:00Z',
  categorization_status: 'UNCATEGORIZED',
};

// Default mock category
const defaultCategory: Category = {
  id: '1',
  name: 'Sample Category',
};

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
};

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
};

// Default mock API client
const defaultMockApiClient: ApiClient = {
  transactions: defaultTransactionClient,
  categories: defaultCategoryClient,
};

// Type for partial overrides of the transaction client
type TransactionClientOverrides = Partial<{
  [K in keyof TransactionClient]: TransactionClient[K];
}>;

// Type for partial overrides of the category client
type CategoryClientOverrides = Partial<{
  [K in keyof CategoryClient]: CategoryClient[K];
}>;

// Type for partial overrides of the API client
interface ApiClientOverrides {
  transactions?: TransactionClientOverrides;
  categories?: CategoryClientOverrides;
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
  };
};
