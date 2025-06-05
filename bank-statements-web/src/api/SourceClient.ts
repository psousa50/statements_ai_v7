import axios from 'axios'
import { Source } from '../types/Transaction'

// Re-export Source type for convenience
export type { Source }

export interface SourceListResponse {
  sources: Source[]
  total: number
}

export interface SourceClient {
  getAll: () => Promise<Source[]>
  createSource: (name: string) => Promise<Source>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/sources`

export const sourceClient: SourceClient = {
  getAll: async (): Promise<Source[]> => {
    const response = await axios.get<{ sources: Source[]; total: number }>(API_URL)
    return response.data.sources
  },

  createSource: async (name: string): Promise<Source> => {
    const response = await axios.post<Source>(API_URL, { name })
    return response.data
  },
}
