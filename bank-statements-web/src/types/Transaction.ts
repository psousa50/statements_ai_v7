export type CategorizationStatus = 'UNCATEGORIZED' | 'CATEGORIZED' | 'FAILURE'

export interface Category {
  id: string
  name: string
  parent_id?: string
}

export interface Source {
  id: string
  name: string
  type?: string
}

export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  source_id?: string
  created_at: string
  category_id?: string
  categorization_status: CategorizationStatus
  running_balance?: number
}

export interface TransactionCreate {
  date: string
  description: string
  amount: number
  source_id?: string
  category_id?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
}
