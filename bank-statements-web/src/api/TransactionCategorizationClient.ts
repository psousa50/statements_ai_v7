import { axiosInstance } from './ApiClient'
import {
  TransactionCategorization,
  TransactionCategorizationCreate,
  TransactionCategorizationFilters,
  TransactionCategorizationListResponse,
  TransactionCategorizationStats,
  TransactionCategorizationUpdate,
} from '../types/TransactionCategorization'

export interface TransactionCategorizationClient {
  getAll(filters?: TransactionCategorizationFilters): Promise<TransactionCategorizationListResponse>
  getStats(): Promise<TransactionCategorizationStats>
  getById(id: string): Promise<TransactionCategorization>
  create(data: TransactionCategorizationCreate): Promise<TransactionCategorization>
  update(id: string, data: TransactionCategorizationUpdate): Promise<TransactionCategorization>
  delete(id: string): Promise<void>
  cleanupUnused(): Promise<{ deleted_count: number; message: string }>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/transaction-categorizations`

export const transactionCategorizationClient: TransactionCategorizationClient = {
  async getAll(filters?: TransactionCategorizationFilters) {
    const params = new URLSearchParams()

    if (filters?.page) {
      params.append('page', filters.page.toString())
    }
    if (filters?.page_size) {
      params.append('page_size', filters.page_size.toString())
    }
    if (filters?.description_search) {
      params.append('description_search', filters.description_search)
    }
    if (filters?.category_ids && filters.category_ids.length > 0) {
      filters.category_ids.forEach((id) => params.append('category_ids', id))
    }
    if (filters?.source) {
      params.append('source', filters.source)
    }
    if (filters?.sort_field) {
      params.append('sort_field', filters.sort_field)
    }
    if (filters?.sort_direction) {
      params.append('sort_direction', filters.sort_direction)
    }

    const url = params.toString() ? `${API_URL}?${params.toString()}` : API_URL
    const response = await axiosInstance.get<TransactionCategorizationListResponse>(url)
    return response.data
  },

  async getStats() {
    const response = await axiosInstance.get<TransactionCategorizationStats>(`${API_URL}/stats`)
    return response.data
  },

  async getById(id: string) {
    const response = await axiosInstance.get<TransactionCategorization>(`${API_URL}/${id}`)
    return response.data
  },

  async create(data: TransactionCategorizationCreate) {
    const response = await axiosInstance.post<TransactionCategorization>(API_URL, data)
    return response.data
  },

  async update(id: string, data: TransactionCategorizationUpdate) {
    const response = await axiosInstance.put<TransactionCategorization>(`${API_URL}/${id}`, data)
    return response.data
  },

  async delete(id: string) {
    await axiosInstance.delete(`${API_URL}/${id}`)
  },

  async cleanupUnused() {
    const response = await axiosInstance.post<{ deleted_count: number; message: string }>(`${API_URL}/cleanup-unused`)
    return response.data
  },
}
