import {
  Transaction,
  TransactionCreate,
  TransactionListResponse,
  CategorizationStatus,
  Source,
} from '../types/Transaction'

export interface TransactionFilters {
  page?: number
  page_size?: number
  category_ids?: string[]
  status?: CategorizationStatus
  min_amount?: number
  max_amount?: number
  description_search?: string
  source_id?: string
  start_date?: string
  end_date?: string
}

export interface CategoryTotal {
  category_id?: string
  total_amount: number
  transaction_count: number
}

export interface CategoryTotalsResponse {
  totals: CategoryTotal[]
}

export interface TransactionClient {
  getAll(filters?: TransactionFilters): Promise<TransactionListResponse>
  getCategoryTotals(filters?: Omit<TransactionFilters, 'page' | 'page_size'>): Promise<CategoryTotalsResponse>
  getById(id: string): Promise<Transaction>
  create(transaction: TransactionCreate): Promise<Transaction>
  update(id: string, transaction: TransactionCreate): Promise<Transaction>
  delete(id: string): Promise<void>
}

export interface SourceClient {
  getAll(): Promise<Source[]>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/transactions`
const SOURCES_API_URL = `${BASE_URL}/api/v1/sources`

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
    if (filters?.source_id) {
      params.append('source_id', filters.source_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }

    const url = params.toString() ? `${API_URL}?${params.toString()}` : API_URL
    const response = await axios.get<TransactionListResponse>(url)
    return response.data
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
    if (filters?.source_id) {
      params.append('source_id', filters.source_id)
    }
    if (filters?.start_date) {
      params.append('start_date', filters.start_date)
    }
    if (filters?.end_date) {
      params.append('end_date', filters.end_date)
    }

    const url = params.toString() ? `${API_URL}/category-totals?${params.toString()}` : `${API_URL}/category-totals`
    const response = await axios.get<CategoryTotalsResponse>(url)
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

  async delete(id: string) {
    await axios.delete(`${API_URL}/${id}`)
  },
}

export const sourceClient: SourceClient = {
  async getAll() {
    const response = await axios.get<Source[]>(SOURCES_API_URL)
    return response.data
  },
}
