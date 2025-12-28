export type CategorizationStatus = 'UNCATEGORIZED' | 'CATEGORIZED' | 'FAILURE'

export interface CategoryParent {
  id: string
  name: string
}

export interface Category {
  id: string
  name: string
  parent_id?: string
  parent?: CategoryParent
}

export interface InitialBalance {
  balance_date: string
  balance_amount: number
}

export interface Account {
  id: string
  name: string
  type?: string
  initial_balance?: InitialBalance
}

export interface Transaction {
  id: string
  date: string
  description: string
  normalized_description: string
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
  account_id: string
  category_id?: string
  counterparty_account_id?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
  total_amount?: number
  enhancement_rule?: import('./EnhancementRule').EnhancementRule
}
