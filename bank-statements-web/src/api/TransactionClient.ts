import { Transaction, TransactionCreate, TransactionListResponse, CategorizationStatus } from '../types/Transaction'

export interface Source {
  id: string
  name: string
}

export interface TransactionFilters {
  page?: number
  page_size?: number
  category_ids?: string[]
  status?: CategorizationStatus
  min_amount?: number
  max_amount?: number
  description_search?: string
  account_id?: string
  start_date?: string
  end_date?: string
  include_running_balance?: boolean
  sort_field?: string
  sort_direction?: 'asc' | 'desc'
  enhancement_rule_id?: string
  exclude_transfers?: boolean
  exclude_uncategorized?: boolean
  transaction_type?: 'all' | 'debit' | 'credit'
  active_only?: boolean
  transaction_ids?: string[]
  saved_filter_id?: string
}

export interface SavedFilterCreate {
  transaction_ids: string[]
}

export interface SavedFilterResponse {
  id: string
  transaction_ids: string[]
}

export interface CategoryTotal {
  category_id?: string
  total_amount: number
  transaction_count: number
}

export interface CategoryTotalsResponse {
  totals: CategoryTotal[]
}

export interface CategoryTimeSeriesDataPoint {
  period: string
  category_id?: string
  total_amount: number
  transaction_count: number
}

export interface CategoryTimeSeriesResponse {
  data_points: CategoryTimeSeriesDataPoint[]
}

export interface BulkUpdateTransactionsRequest {
  normalized_description: string
  category_id?: string
}

export interface BulkUpdateTransactionsResponse {
  updated_count: number
  message: string
}

export interface CountSimilarFilters {
  normalized_description: string
  account_id?: string
  start_date?: string
  end_date?: string
  exclude_transfers?: boolean
}

export interface CountSimilarResponse {
  count: number
}

export interface CountByCategoryFilters {
  category_id: string
  account_id?: string
  start_date?: string
  end_date?: string
  exclude_transfers?: boolean
}

export interface BulkReplaceCategoryRequest {
  from_category_id: string
  to_category_id?: string
  account_id?: string
  start_date?: string
  end_date?: string
  exclude_transfers?: boolean
}

export interface BulkReplaceCategoryResponse {
  updated_count: number
  message: string
}

export interface EnhancementPreviewRequest {
  description: string
  amount?: number
  transaction_date?: string
}

export interface EnhancementPreviewResponse {
  matched: boolean
  rule_pattern?: string
  category_id?: string
  category_name?: string
  counterparty_account_id?: string
  counterparty_account_name?: string
}

export interface RecurringPattern {
  description: string
  normalized_description: string
  interval_days: number
  average_amount: number
  amount_variance: number
  transaction_count: number
  transaction_ids: string[]
  category_id?: string
  first_transaction_date: string
  last_transaction_date: string
  total_annual_cost: number
}

export interface RecurringPatternsResponse {
  patterns: RecurringPattern[]
  summary: {
    total_monthly_recurring: number
    pattern_count: number
  }
}

export interface TransactionClient {
  getAll(filters?: TransactionFilters): Promise<TransactionListResponse>
  exportCSV(filters?: Omit<TransactionFilters, 'page' | 'page_size'>): Promise<void>
  getCategoryTotals(filters?: Omit<TransactionFilters, 'page' | 'page_size'>): Promise<CategoryTotalsResponse>
  getCategoryTimeSeries(
    categoryId?: string,
    period?: 'month' | 'week',
    filters?: Omit<TransactionFilters, 'page' | 'page_size'>
  ): Promise<CategoryTimeSeriesResponse>
  getRecurringPatterns(activeOnly?: boolean): Promise<RecurringPatternsResponse>
  getById(id: string): Promise<Transaction>
  create(transaction: TransactionCreate): Promise<Transaction>
  update(id: string, transaction: TransactionCreate): Promise<Transaction>
  categorize(id: string, categoryId?: string): Promise<Transaction>
  delete(id: string): Promise<void>
  bulkUpdateCategory(request: BulkUpdateTransactionsRequest): Promise<BulkUpdateTransactionsResponse>
  countSimilar(filters: CountSimilarFilters): Promise<CountSimilarResponse>
  countByCategory(filters: CountByCategoryFilters): Promise<CountSimilarResponse>
  bulkReplaceCategory(request: BulkReplaceCategoryRequest): Promise<BulkReplaceCategoryResponse>
  previewEnhancement(request: EnhancementPreviewRequest): Promise<EnhancementPreviewResponse>
  createSavedFilter(transactionIds: string[]): Promise<SavedFilterResponse>
}

export interface SourceClient {
  getAll(): Promise<Source[]>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/transactions`
const SOURCES_API_URL = `${BASE_URL}/api/v1/sources`
const SAVED_FILTERS_API_URL = `${BASE_URL}/api/v1/saved-filters`

import axios from 'axios'

export const transactionClient: TransactionClient = {
  async getAll(filters?: TransactionFilters) {
    const params = new URLSearchParams()

    if (filters?.page) {
      params.append('page', filters.page.toString())
    }
    if (filters?.page_size) {
      params.append('page_size', filters.page_size.toString())
    }
    if (filters?.category_ids && filters.category_ids.length > 0) {
      params.append('category_ids', filters.category_ids.join(','))
    }
    if (filters?.status) {
      params.append('status', filters.status)
    }
    if (filters?.min_amount !== undefined) {
      params.append('min_amount', filters.min_amount.toString())
    }
    if (filters?.max_amount !== undefined) {
      params.append('max_amount', filters.max_amount.toString())
    }
    if (filters?.description_search) {
      params.append('description_search', filters.description_search)
    }
    if (filters?.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters?.include_running_balance) {
      params.append('include_running_balance', 'true')
    }
    if (filters?.sort_field) {
      params.append('sort_field', filters.sort_field)
    }
    if (filters?.sort_direction) {
      params.append('sort_direction', filters.sort_direction)
    }
    if (filters?.enhancement_rule_id) {
      params.append('enhancement_rule_id', filters.enhancement_rule_id)
    }
    if (filters?.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    if (filters?.exclude_uncategorized !== undefined) {
      params.append('exclude_uncategorized', filters.exclude_uncategorized.toString())
    }
    if (filters?.transaction_type) {
      params.append('transaction_type', filters.transaction_type)
    }
    if (filters?.transaction_ids && filters.transaction_ids.length > 0) {
      params.append('transaction_ids', filters.transaction_ids.join(','))
    }
    if (filters?.saved_filter_id) {
      params.append('saved_filter_id', filters.saved_filter_id)
    }

    const url = params.toString() ? `${API_URL}?${params.toString()}` : API_URL
    const response = await axios.get<TransactionListResponse>(url)
    return response.data
  },

  async exportCSV(filters?: Omit<TransactionFilters, 'page' | 'page_size'>) {
    const params = new URLSearchParams()

    if (filters?.category_ids && filters.category_ids.length > 0) {
      params.append('category_ids', filters.category_ids.join(','))
    }
    if (filters?.status) {
      params.append('status', filters.status)
    }
    if (filters?.min_amount !== undefined) {
      params.append('min_amount', filters.min_amount.toString())
    }
    if (filters?.max_amount !== undefined) {
      params.append('max_amount', filters.max_amount.toString())
    }
    if (filters?.description_search) {
      params.append('description_search', filters.description_search)
    }
    if (filters?.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters?.sort_field) {
      params.append('sort_field', filters.sort_field)
    }
    if (filters?.sort_direction) {
      params.append('sort_direction', filters.sort_direction)
    }
    if (filters?.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    if (filters?.exclude_uncategorized !== undefined) {
      params.append('exclude_uncategorized', filters.exclude_uncategorized.toString())
    }
    if (filters?.transaction_type) {
      params.append('transaction_type', filters.transaction_type)
    }

    const url = params.toString() ? `${API_URL}/export?${params.toString()}` : `${API_URL}/export`
    const response = await axios.get(url, { responseType: 'blob' })

    const contentDisposition = response.headers['content-disposition']
    let filename = 'transactions.csv'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="(.+)"/)
      if (match) {
        filename = match[1]
      }
    }

    const blob = new Blob([response.data], { type: 'text/csv' })
    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(downloadUrl)
  },

  async getCategoryTotals(filters?: Omit<TransactionFilters, 'page' | 'page_size'>) {
    const params = new URLSearchParams()

    if (filters?.category_ids && filters.category_ids.length > 0) {
      params.append('category_ids', filters.category_ids.join(','))
    }
    if (filters?.status) {
      params.append('status', filters.status)
    }
    if (filters?.min_amount !== undefined) {
      params.append('min_amount', filters.min_amount.toString())
    }
    if (filters?.max_amount !== undefined) {
      params.append('max_amount', filters.max_amount.toString())
    }
    if (filters?.description_search) {
      params.append('description_search', filters.description_search)
    }
    if (filters?.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters?.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    if (filters?.exclude_uncategorized !== undefined) {
      params.append('exclude_uncategorized', filters.exclude_uncategorized.toString())
    }
    if (filters?.transaction_type) {
      params.append('transaction_type', filters.transaction_type)
    }

    const url = params.toString() ? `${API_URL}/category-totals?${params.toString()}` : `${API_URL}/category-totals`
    const response = await axios.get<CategoryTotalsResponse>(url)
    return response.data
  },

  async getCategoryTimeSeries(
    categoryId?: string,
    period: 'month' | 'week' = 'month',
    filters?: Omit<TransactionFilters, 'page' | 'page_size'>
  ) {
    const params = new URLSearchParams()

    if (categoryId) {
      params.append('category_id', categoryId)
    }
    params.append('period', period)

    if (filters?.category_ids && filters.category_ids.length > 0) {
      params.append('category_ids', filters.category_ids.join(','))
    }
    if (filters?.status) {
      params.append('status', filters.status)
    }
    if (filters?.min_amount !== undefined) {
      params.append('min_amount', filters.min_amount.toString())
    }
    if (filters?.max_amount !== undefined) {
      params.append('max_amount', filters.max_amount.toString())
    }
    if (filters?.description_search) {
      params.append('description_search', filters.description_search)
    }
    if (filters?.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters?.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    if (filters?.exclude_uncategorized !== undefined) {
      params.append('exclude_uncategorized', filters.exclude_uncategorized.toString())
    }
    if (filters?.transaction_type) {
      params.append('transaction_type', filters.transaction_type)
    }

    const url = params.toString()
      ? `${API_URL}/category-time-series?${params.toString()}`
      : `${API_URL}/category-time-series`
    const response = await axios.get<CategoryTimeSeriesResponse>(url)
    return response.data
  },

  async getRecurringPatterns(activeOnly: boolean = true) {
    const params = new URLSearchParams()
    params.append('active_only', activeOnly.toString())

    const response = await axios.get<RecurringPatternsResponse>(`${API_URL}/recurring-patterns?${params.toString()}`)
    return response.data
  },

  async getById(id: string) {
    const response = await axios.get<Transaction>(`${API_URL}/${id}`)
    return response.data
  },

  async create(transaction: TransactionCreate) {
    const response = await axios.post<Transaction>(API_URL, transaction)
    return response.data
  },

  async update(id: string, transaction: TransactionCreate) {
    const response = await axios.put<Transaction>(`${API_URL}/${id}`, transaction)
    return response.data
  },

  async categorize(id: string, categoryId?: string) {
    const params = new URLSearchParams()
    if (categoryId) {
      params.append('category_id', categoryId)
    }
    const url = params.toString() ? `${API_URL}/${id}/categorize?${params.toString()}` : `${API_URL}/${id}/categorize`
    const response = await axios.put<Transaction>(url)
    return response.data
  },

  async delete(id: string) {
    await axios.delete(`${API_URL}/${id}`)
  },

  async bulkUpdateCategory(request: BulkUpdateTransactionsRequest) {
    const response = await axios.put<BulkUpdateTransactionsResponse>(`${API_URL}/bulk-update-category`, request)
    return response.data
  },

  async countSimilar(filters: CountSimilarFilters) {
    const params = new URLSearchParams()
    params.append('normalized_description', filters.normalized_description)
    if (filters.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    const response = await axios.get<CountSimilarResponse>(`${API_URL}/count-similar?${params.toString()}`)
    return response.data
  },

  async countByCategory(filters: CountByCategoryFilters) {
    const params = new URLSearchParams()
    params.append('category_id', filters.category_id)
    if (filters.account_id) {
      params.append('account_id', filters.account_id)
    }
    if (filters.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters.end_date) {
      params.append('end_date', filters.end_date)
    }
    if (filters.exclude_transfers !== undefined) {
      params.append('exclude_transfers', filters.exclude_transfers.toString())
    }
    const response = await axios.get<CountSimilarResponse>(`${API_URL}/count-by-category?${params.toString()}`)
    return response.data
  },

  async bulkReplaceCategory(request: BulkReplaceCategoryRequest) {
    const response = await axios.put<BulkReplaceCategoryResponse>(`${API_URL}/bulk-replace-category`, request)
    return response.data
  },

  async previewEnhancement(request: EnhancementPreviewRequest) {
    const response = await axios.post<EnhancementPreviewResponse>(`${API_URL}/preview-enhancement`, request)
    return response.data
  },

  async createSavedFilter(transactionIds: string[]) {
    const response = await axios.post<SavedFilterResponse>(SAVED_FILTERS_API_URL, {
      transaction_ids: transactionIds,
    })
    return response.data
  },
}

export const sourceClient: SourceClient = {
  async getAll() {
    const response = await axios.get<Source[]>(SOURCES_API_URL)
    return response.data
  },
}
