import axios from 'axios'
import {
  AIApplySuggestionRequest,
  AIApplySuggestionResponse,
  AISuggestCategoriesRequest,
  AISuggestCategoriesResponse,
  EnhancementRule,
  EnhancementRuleCreate,
  EnhancementRuleFilters,
  EnhancementRuleListResponse,
  EnhancementRuleStats,
  EnhancementRuleUpdate,
  MatchingTransactionsCountResponse,
} from '../types/EnhancementRule'

export interface EnhancementRuleClient {
  getAll(filters?: EnhancementRuleFilters): Promise<EnhancementRuleListResponse>
  getStats(): Promise<EnhancementRuleStats>
  getById(id: string): Promise<EnhancementRule>
  getMatchingTransactionsCount(id: string): Promise<MatchingTransactionsCountResponse>
  previewMatchingTransactionsCount(data: EnhancementRuleCreate): Promise<MatchingTransactionsCountResponse>
  create(data: EnhancementRuleCreate): Promise<EnhancementRule>
  update(id: string, data: EnhancementRuleUpdate): Promise<EnhancementRule>
  delete(id: string): Promise<void>
  cleanupUnused(): Promise<{ deleted_count: number; message: string }>
  suggestCategories(request: AISuggestCategoriesRequest): Promise<AISuggestCategoriesResponse>
  suggestCounterparties(request: AISuggestCategoriesRequest): Promise<AISuggestCategoriesResponse>
  applySuggestion(ruleId: string, request: AIApplySuggestionRequest): Promise<AIApplySuggestionResponse>
  rejectSuggestion(ruleId: string): Promise<AIApplySuggestionResponse>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/enhancement-rules`

export const enhancementRuleClient: EnhancementRuleClient = {
  async getAll(filters?: EnhancementRuleFilters) {
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
    if (filters?.counterparty_account_ids && filters.counterparty_account_ids.length > 0) {
      filters.counterparty_account_ids.forEach((id) => params.append('counterparty_account_ids', id))
    }
    if (filters?.match_type) {
      params.append('match_type', filters.match_type)
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
    if (filters?.show_invalid_only) {
      params.append('show_invalid_only', 'true')
    }
    if (filters?.has_pending_suggestions) {
      params.append('has_pending_suggestions', 'true')
    }

    const url = params.toString() ? `${API_URL}?${params.toString()}` : API_URL
    const response = await axios.get<EnhancementRuleListResponse>(url)
    return response.data
  },

  async getStats() {
    const response = await axios.get<EnhancementRuleStats>(`${API_URL}/stats`)
    return response.data
  },

  async getById(id: string) {
    const response = await axios.get<EnhancementRule>(`${API_URL}/${id}`)
    return response.data
  },

  async getMatchingTransactionsCount(id: string) {
    const response = await axios.get<MatchingTransactionsCountResponse>(`${API_URL}/${id}/matching-transactions/count`)
    return response.data
  },

  async previewMatchingTransactionsCount(data: EnhancementRuleCreate) {
    const response = await axios.post<MatchingTransactionsCountResponse>(
      `${API_URL}/preview/matching-transactions/count`,
      data
    )
    return response.data
  },

  async create(data: EnhancementRuleCreate) {
    const response = await axios.post<EnhancementRule>(API_URL, data)
    return response.data
  },

  async update(id: string, data: EnhancementRuleUpdate) {
    const response = await axios.put<EnhancementRule>(`${API_URL}/${id}`, data)
    return response.data
  },

  async delete(id: string) {
    await axios.delete(`${API_URL}/${id}`)
  },

  async cleanupUnused() {
    const response = await axios.post<{ deleted_count: number; message: string }>(`${API_URL}/cleanup-unused`)
    return response.data
  },

  async suggestCategories(request: AISuggestCategoriesRequest) {
    const response = await axios.post<AISuggestCategoriesResponse>(`${API_URL}/ai/suggest-categories`, request)
    return response.data
  },

  async suggestCounterparties(request: AISuggestCategoriesRequest) {
    const response = await axios.post<AISuggestCategoriesResponse>(`${API_URL}/ai/suggest-counterparties`, request)
    return response.data
  },

  async applySuggestion(ruleId: string, request: AIApplySuggestionRequest) {
    const response = await axios.post<AIApplySuggestionResponse>(`${API_URL}/${ruleId}/ai-suggestion/apply`, request)
    return response.data
  },

  async rejectSuggestion(ruleId: string) {
    const response = await axios.post<AIApplySuggestionResponse>(`${API_URL}/${ruleId}/ai-suggestion/reject`)
    return response.data
  },
}
