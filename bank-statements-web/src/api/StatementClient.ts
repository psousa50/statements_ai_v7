import axios from 'axios'

export interface ColumnMapping {
  date: string
  amount: string
  description: string
  category?: string
}

export type SampleData = string[][]

export interface StatementAnalysisResponse {
  uploaded_file_id: string
  file_type: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  sample_data: string[][]
  source_id?: string
  total_transactions: number
  unique_transactions: number
  duplicate_transactions: number
  date_range: [string, string]
  total_amount: number
  total_debit: number
  total_credit: number
}

export interface StatementUploadRequest {
  source_id: string
  uploaded_file_id: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
}

export interface StatementUploadResponse {
  uploaded_file_id: string
  transactions_saved: number
  duplicated_transactions: number
  success: boolean
  message: string

  // Synchronous categorization results
  total_processed: number
  rule_based_matches: number
  match_rate_percentage: number
  processing_time_ms: number

  // Background job information (if unmatched transactions exist)
  background_job?: {
    job_id: string
    status: string
    remaining_transactions: number
    estimated_completion_seconds?: number
    status_url: string
  }

  sample_data?: SampleData[]
}

export interface StatementClient {
  analyzeStatement: (file: File) => Promise<StatementAnalysisResponse>
  uploadStatement: (data: StatementUploadRequest) => Promise<StatementUploadResponse>
}

export const statementClient: StatementClient = {
  analyzeStatement: async (file: File): Promise<StatementAnalysisResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post<StatementAnalysisResponse>('/api/v1/statements/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  uploadStatement: async (data: StatementUploadRequest): Promise<StatementUploadResponse> => {
    const response = await axios.post<StatementUploadResponse>('/api/v1/statements/upload', data)
    return response.data
  },
}
