import axios from 'axios'

export interface ColumnMapping {
  date: string
  amount: string
  description: string
  category?: string
}

export interface SampleData {
  date: string
  amount: number
  description: string
  category?: string
}

export interface StatementAnalysisResponse {
  uploaded_file_id: string
  file_type: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  sample_data: Record<string, unknown>[]
  file_hash: string
}

export interface StatementUploadRequest {
  uploaded_file_id: string
  file_type: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  file_hash: string
  source?: string
}

export interface StatementUploadResponse {
  uploaded_file_id: string
  transactions_saved: number
  success: boolean
  message: string
}

export interface StatementClient {
  analyzeStatement: (file: File) => Promise<StatementAnalysisResponse>
  uploadStatement: (data: StatementUploadRequest) => Promise<StatementUploadResponse>
}

export const statementClient: StatementClient = {
  analyzeStatement: async (file: File): Promise<StatementAnalysisResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post<StatementAnalysisResponse>(
      '/api/v1/statements/analyze',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  uploadStatement: async (data: StatementUploadRequest): Promise<StatementUploadResponse> => {
    const response = await axios.post<StatementUploadResponse>('/api/v1/statements/upload', data)
    return response.data
  },
}
