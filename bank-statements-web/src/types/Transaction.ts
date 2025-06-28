export type CategorizationStatus = 'UNCATEGORIZED' | 'CATEGORIZED' | 'FAILURE'

export interface Category {
  id: string
  name: string
  parent_id?: string
}

export interface Account {
  id: string
  name: string
  type?: string
}

export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  account_id?: string
  created_at: string
  category_id?: string
  categorization_status: CategorizationStatus
  running_balance?: number
  counterparty_account_id?: string
  counterparty_status?: 'UNPROCESSED' | 'INFERRED' | 'CONFIRMED'
}

export interface TransactionCreate {
  date: string
  description: string
  amount: number
  account_id?: string
  category_id?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
  enhancement_rule?: import('./EnhancementRule').EnhancementRule
}
