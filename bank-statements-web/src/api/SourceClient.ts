import axios from 'axios'

export interface Source {
  id: string
  name: string
}

export interface SourceListResponse {
  sources: Source[]
  total: number
}

export interface SourceClient {
  getSources: () => Promise<SourceListResponse>
  createSource: (name: string) => Promise<Source>
}

export const sourceClient: SourceClient = {
  getSources: async (): Promise<SourceListResponse> => {
    const response = await axios.get<SourceListResponse>('/api/v1/sources')
    return response.data
  },

  createSource: async (name: string): Promise<Source> => {
    const response = await axios.post<Source>('/api/v1/sources', { name })
    return response.data
  },
}
