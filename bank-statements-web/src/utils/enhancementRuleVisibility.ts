import { EnhancementRule, EnhancementRuleFilters } from '../types/EnhancementRule'

export const ruleHiddenReason = (rule: EnhancementRule, filters: EnhancementRuleFilters): string | null => {
  const status = filters.rule_status_filter
  if (status === 'unconfigured' && (rule.category_id || rule.counterparty_account_id)) {
    return 'the "Unconfigured" filter'
  }
  if (
    (status === 'pending' || status === 'applied') &&
    !rule.ai_suggested_category_id &&
    !rule.ai_suggested_counterparty_id
  ) {
    return `the "${status === 'pending' ? 'Pending' : 'Applied'}" filter`
  }
  if (filters.category_ids?.length && (!rule.category_id || !filters.category_ids.includes(rule.category_id))) {
    return 'the category filter'
  }
  if (
    filters.counterparty_account_ids?.length &&
    (!rule.counterparty_account_id || !filters.counterparty_account_ids.includes(rule.counterparty_account_id))
  ) {
    return 'the counterparty filter'
  }
  if (filters.source && rule.source !== filters.source) {
    return 'the source filter'
  }
  if (filters.match_type && !rule.patterns.some((p) => p.match_type === filters.match_type)) {
    return 'the match-type filter'
  }
  if (filters.description_search) {
    const needle = filters.description_search.toLowerCase()
    if (!rule.patterns.some((p) => p.normalized_description.toLowerCase().includes(needle))) {
      return 'the description search'
    }
  }
  return null
}
