import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export interface ColumnMapping {
  date: string
  amount: string
  description: string
  category?: string
}

export type SampleData = string[][]

export enum FilterOperator {
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  EQUALS = 'equals',
  NOT_EQUALS = 'not_equals',
  GREATER_THAN = 'greater_than',
  LESS_THAN = 'less_than',
  GREATER_THAN_OR_EQUAL = 'greater_than_or_equal',
  LESS_THAN_OR_EQUAL = 'less_than_or_equal',
  REGEX = 'regex',
  IS_EMPTY = 'is_empty',
  IS_NOT_EMPTY = 'is_not_empty',
}

export enum LogicalOperator {
  AND = 'and',
  OR = 'or',
}

export interface FilterCondition {
  column_name: string
  operator: FilterOperator
  value?: string
  case_sensitive: boolean
}

export interface RowFilter {
  conditions: FilterCondition[]
  logical_operator: LogicalOperator
}

export interface StatementAnalysisResponse {
  uploaded_file_id: string
  file_type: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  sample_data: string[][]
  account_id?: string
  total_transactions: number
  unique_transactions: number
  duplicate_transactions: number
  date_range: [string, string]
  total_amount: number
  total_debit: number
  total_credit: number
  suggested_filters?: FilterCondition[]
  saved_row_filters?: FilterCondition[]
}

export interface StatementUploadRequest {
  account_id: string
  uploaded_file_id: string
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  row_filters?: RowFilter | null
}

export interface FilterPreviewResponse {
  total_rows: number
  included_rows: number
  excluded_rows: number
  included_row_indices: number[]
  excluded_row_indices: number[]
}

export interface StatisticsPreviewRequest {
  column_mapping: Record<string, string>
  header_row_index: number
  data_start_row_index: number
  row_filters?: RowFilter | null
  account_id?: string
}

export interface StatisticsPreviewResponse {
  total_transactions: number
  unique_transactions: number
  duplicate_transactions: number
  date_range: [string, string]
  total_amount: number
  total_debit: number
  total_credit: number
  filter_preview?: FilterPreviewResponse
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

export interface StatementResponse {
  id: string
  account_id: string
  account_name: string
  filename: string
  file_type: string
  transaction_count: number | null
  date_from: string | null
  date_to: string | null
  created_at: string
}

export interface StatementClient {
  analyzeStatement: (file: File) => Promise<StatementAnalysisResponse>
  uploadStatement: (data: StatementUploadRequest) => Promise<StatementUploadResponse>
  previewStatistics: (uploadedFileId: string, data: StatisticsPreviewRequest) => Promise<StatisticsPreviewResponse>
  listStatements: () => Promise<StatementResponse[]>
  deleteStatement: (statementId: string) => Promise<{ message: string }>
}

export const statementClient: StatementClient = {
  analyzeStatement: async (file: File): Promise<StatementAnalysisResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post<StatementAnalysisResponse>(`${BASE_URL}/api/v1/statements/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  uploadStatement: async (data: StatementUploadRequest): Promise<StatementUploadResponse> => {
    const response = await axios.post<StatementUploadResponse>(`${BASE_URL}/api/v1/statements/upload`, data)
    return response.data
  },

  previewStatistics: async (
    uploadedFileId: string,
    data: StatisticsPreviewRequest
  ): Promise<StatisticsPreviewResponse> => {
    const response = await axios.post<StatisticsPreviewResponse>(
      `${BASE_URL}/api/v1/statements/${uploadedFileId}/preview-statistics`,
      data
    )
    return response.data
  },

  listStatements: async (): Promise<StatementResponse[]> => {
    const response = await axios.get<StatementResponse[]>(`${BASE_URL}/api/v1/statements`)
    return response.data
  },

  deleteStatement: async (statementId: string): Promise<{ message: string }> => {
    const response = await axios.delete<{ message: string }>(`${BASE_URL}/api/v1/statements/${statementId}`)
    return response.data
  },
}
