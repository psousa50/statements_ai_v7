import { Category } from './Transaction'

export enum CategorizationSource {
  MANUAL = 'MANUAL',
  AI = 'AI',
}

export interface TransactionCategorization {
  id: string
  normalized_description: string
  category_id: string
  source: CategorizationSource
  created_at: string
  updated_at: string
  category?: Category
  transaction_count?: number
}

export interface TransactionCategorizationCreate {
  normalized_description: string
  category_id: string
  source: CategorizationSource
}

export interface TransactionCategorizationUpdate {
  normalized_description: string
  category_id: string
  source: CategorizationSource
}

export interface TransactionCategorizationListResponse {
  categorizations: TransactionCategorization[]
  total: number
}

export type SortField = 'normalized_description' | 'category' | 'usage' | 'source' | 'created_at'
export type SortDirection = 'asc' | 'desc'

export interface TransactionCategorizationFilters {
  page?: number
  page_size?: number
  description_search?: string
  category_ids?: string[]
  source?: CategorizationSource
  sort_field?: SortField
  sort_direction?: SortDirection
}

export interface CategoryUsage {
  category_id: string
  category_name: string
  parent_category_name?: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  ai_rules: number
}

export interface TopRule {
  rule_id: string
  normalized_description: string
  category_name: string
  transaction_count: number
  source: string
}

export interface UnusedRule {
  rule_id: string
  normalized_description: string
  category_name: string
  source: string
  created_at: string
}

export interface TransactionCategorizationStats {
  summary: {
    total_rules: number
    manual_rules: number
    ai_rules: number
    total_transactions_categorized: number
    transactions_with_manual_rules: number
    transactions_with_ai_rules: number
  }
  category_usage: CategoryUsage[]
  top_rules_by_usage: TopRule[]
  unused_rules: UnusedRule[]
}
