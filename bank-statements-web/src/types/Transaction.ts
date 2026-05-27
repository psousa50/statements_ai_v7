export type CategorizationStatus = 'UNCATEGORIZED' | 'CATEGORIZED' | 'FAILURE'

export interface CategoryParent {
  id: string
  name: string
  color?: string
}

export interface Category {
  id: string
  name: string
  color?: string
  parent_id?: string
  parent?: CategoryParent
  kind: CategoryKind
  priority: CategoryPriority
  is_regular: boolean
}

export type CategoryKind = 'expense' | 'income' | 'transfer' | 'reimbursable'

export const CATEGORY_KIND_LABELS: Record<CategoryKind, string> = {
  expense: 'Expense',
  income: 'Income',
  transfer: 'Transfer',
  reimbursable: 'Reimbursable',
}

export const CATEGORY_KIND_DESCRIPTIONS: Record<CategoryKind, string> = {
  expense: 'Money actually leaves (food, housing, transport, loans).',
  income: 'Money actually comes in (salary, dividends, gifts).',
  transfer: 'Movement between your own accounts; no effect on net worth.',
  reimbursable: 'You pay then get refunded; nets to zero.',
}

export type CategoryPriority = 'need' | 'comfort' | 'unplanned' | 'extra'

export const CATEGORY_PRIORITY_LABELS: Record<CategoryPriority, string> = {
  need: 'Need',
  comfort: 'Comfort',
  unplanned: 'Unplanned',
  extra: 'Extra',
}

export const CATEGORY_PRIORITY_DESCRIPTIONS: Record<CategoryPriority, string> = {
  need: 'Essential ongoing spending (rent, groceries, utilities).',
  comfort: 'Ongoing but cuttable (subscriptions, gym, takeaway).',
  unplanned: 'One-off necessities (repairs, projects, medical).',
  extra: 'One-off treats (travel, shopping sprees).',
}

export interface InitialBalance {
  balance_date: string
  balance_amount: number
}

export interface Account {
  id: string
  name: string
  currency: string
  type?: string
  initial_balance?: InitialBalance
}

export interface Tag {
  id: string
  name: string
  created_at: string
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
  tags?: Tag[]
  exclude_from_analytics: boolean
  is_split_parent: boolean
  is_split_child: boolean
  parent_transaction_id?: string
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
