export type CategorizationStatus = 'UNCATEGORIZED' | 'CATEGORIZED' | 'FAILURE'

export interface Category {
  id: string
  name: string
  parent_id?: string
}

export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  created_at: string
  category_id?: string
  categorization_status: CategorizationStatus
}

export interface TransactionCreate {
  date: string
  description: string
  amount: number
  category_id?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
}
