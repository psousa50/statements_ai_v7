import { Category } from './Transaction'

export enum EnhancementRuleSource {
  MANUAL = 'MANUAL',
  AI = 'AI',
}

export enum MatchType {
  EXACT = 'exact',
  PREFIX = 'prefix',
  INFIX = 'infix',
}

export interface EnhancementRule {
  id: string
  normalized_description_pattern: string
  match_type: MatchType
  category_id?: string
  counterparty_account_id?: string
  min_amount?: number
  max_amount?: number
  start_date?: string
  end_date?: string
  source: EnhancementRuleSource
  created_at: string
  updated_at: string
  // Populated from joins
  category?: Category
  counterparty_account?: {
    id: string
    name: string
    account_number?: string
  }
  transaction_count?: number
}

export interface EnhancementRuleCreate {
  normalized_description_pattern: string
  match_type: MatchType
  category_id?: string
  counterparty_account_id?: string
  min_amount?: number
  max_amount?: number
  start_date?: string
  end_date?: string
  source: EnhancementRuleSource
}

export interface EnhancementRuleUpdate {
  normalized_description_pattern: string
  match_type: MatchType
  category_id?: string
  counterparty_account_id?: string
  min_amount?: number
  max_amount?: number
  start_date?: string
  end_date?: string
  source: EnhancementRuleSource
  apply_to_existing?: boolean
}

export interface MatchingTransactionsCountResponse {
  count: number
  date_range?: [string, string]
  amount_range?: [number, number]
}

export interface EnhancementRuleListResponse {
  rules: EnhancementRule[]
  total: number
}

export type SortField =
  | 'normalized_description_pattern'
  | 'category'
  | 'counterparty'
  | 'usage'
  | 'source'
  | 'created_at'
export type SortDirection = 'asc' | 'desc'

export interface EnhancementRuleFilters {
  page?: number
  page_size?: number
  description_search?: string
  category_ids?: string[]
  counterparty_account_ids?: string[]
  match_type?: MatchType
  source?: EnhancementRuleSource
  sort_field?: SortField
  sort_direction?: SortDirection
}

export interface RuleTypeUsage {
  rule_type: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  ai_rules: number
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

export interface CounterpartyUsage {
  counterparty_account_id: string
  counterparty_name: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  ai_rules: number
}

export interface TopRule {
  rule_id: string
  normalized_description: string
  category_name?: string
  counterparty_name?: string
  transaction_count: number
  source: string
  rule_type: string // 'Category Only', 'Counterparty Only', 'Category + Counterparty'
}

export interface UnusedRule {
  rule_id: string
  normalized_description: string
  category_name?: string
  counterparty_name?: string
  source: string
  created_at: string
  rule_type: string
}

export interface EnhancementRuleStats {
  summary: {
    total_rules: number
    manual_rules: number
    ai_rules: number
    category_only_rules: number
    counterparty_only_rules: number
    combined_rules: number
    total_transactions_enhanced: number
    transactions_with_manual_rules: number
    transactions_with_ai_rules: number
  }
  rule_type_usage: RuleTypeUsage[]
  category_usage: CategoryUsage[]
  counterparty_usage: CounterpartyUsage[]
  top_rules_by_usage: TopRule[]
  unused_rules: UnusedRule[]
}
