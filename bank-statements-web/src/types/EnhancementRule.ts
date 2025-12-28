import { Category } from './Transaction'

export enum EnhancementRuleSource {
  MANUAL = 'MANUAL',
  AUTO = 'AUTO',
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
  rule_type: string
  // Populated from joins
  category?: Category
  counterparty_account?: {
    id: string
    name: string
    account_number?: string
  }
  transaction_count?: number
  pending_transaction_count?: number
  // AI suggestion fields
  ai_suggested_category_id?: string
  ai_category_confidence?: number
  ai_suggested_counterparty_id?: string
  ai_counterparty_confidence?: number
  ai_processed_at?: string
  ai_suggested_category?: Category
  ai_suggested_counterparty?: {
    id: string
    name: string
    account_number?: string
  }
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

export type RuleStatusFilter = 'unconfigured' | 'pending' | 'applied'

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
  rule_status_filter?: RuleStatusFilter
}

export interface RuleTypeUsage {
  rule_type: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  auto_rules: number
}

export interface CategoryUsage {
  category_id: string
  category_name: string
  parent_category_name?: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  auto_rules: number
}

export interface CounterpartyUsage {
  counterparty_account_id: string
  counterparty_name: string
  rule_count: number
  transaction_count: number
  manual_rules: number
  auto_rules: number
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
    auto_rules: number
    category_only_rules: number
    counterparty_only_rules: number
    combined_rules: number
    total_transactions_enhanced: number
    transactions_with_manual_rules: number
    transactions_with_auto_rules: number
  }
  rule_type_usage: RuleTypeUsage[]
  category_usage: CategoryUsage[]
  counterparty_usage: CounterpartyUsage[]
  top_rules_by_usage: TopRule[]
  unused_rules: UnusedRule[]
}

export interface AISuggestCategoriesRequest {
  rule_ids?: string[]
  confidence_threshold?: number
  auto_apply?: boolean
}

export interface AISuggestCategoriesResponse {
  processed: number
  auto_applied: number
  suggestions: number
  failed: number
  error_message?: string
}

export interface AIApplySuggestionRequest {
  apply_to_transactions?: boolean
}

export interface AIApplySuggestionResponse {
  rule_id: string
  applied: boolean
  transactions_updated: number
}
