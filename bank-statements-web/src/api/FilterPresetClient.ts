import { axiosInstance } from './ApiClient'

export interface FilterPresetData {
  category_ids?: string[]
  account_id?: string
  min_amount?: number
  max_amount?: number
  description_search?: string
  start_date?: string
  end_date?: string
  exclude_transfers?: boolean
  categorization_filter?: 'all' | 'categorized' | 'uncategorized'
  transaction_type?: 'all' | 'debit' | 'credit'
  sort_field?: 'date' | 'amount' | 'description' | 'created_at'
  sort_direction?: 'asc' | 'desc'
}

export interface FilterPreset {
  id: string
  name: string
  filter_data: FilterPresetData
  created_at: string
  updated_at: string
}

export interface FilterPresetClient {
  getAll: () => Promise<FilterPreset[]>
  create: (name: string, filterData: FilterPresetData) => Promise<FilterPreset>
  delete: (id: string) => Promise<void>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/filter-presets`

export const filterPresetClient: FilterPresetClient = {
  getAll: async (): Promise<FilterPreset[]> => {
    const response = await axiosInstance.get<{ presets: FilterPreset[]; total: number }>(API_URL)
    return response.data.presets
  },

  create: async (name: string, filterData: FilterPresetData): Promise<FilterPreset> => {
    const response = await axiosInstance.post<FilterPreset>(API_URL, {
      name,
      filter_data: filterData,
    })
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await axiosInstance.delete(`${API_URL}/${id}`)
  },
}
