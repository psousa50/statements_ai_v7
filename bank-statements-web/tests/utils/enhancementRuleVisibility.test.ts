import { expect, test, describe } from 'vitest'
import { ruleHiddenReason } from '@/utils/enhancementRuleVisibility'
import { EnhancementRule, EnhancementRuleFilters, EnhancementRuleSource, MatchType } from '@/types/EnhancementRule'

const createRule = (overrides: Partial<EnhancementRule> = {}): EnhancementRule => ({
  id: 'rule-1',
  patterns: [{ id: 'p1', normalized_description: 'to pocket eur savings', match_type: MatchType.INFIX, sort_order: 0 }],
  source: EnhancementRuleSource.MANUAL,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  rule_type: 'Category + Counterparty',
  ...overrides,
})

describe('ruleHiddenReason', () => {
  test('configured rule is hidden by the unconfigured filter', () => {
    const rule = createRule({ category_id: 'cat-1', counterparty_account_id: 'acc-1' })
    const filters: EnhancementRuleFilters = { rule_status_filter: 'unconfigured' }

    expect(ruleHiddenReason(rule, filters)).toBe('the "Unconfigured" filter')
  })

  test('unconfigured rule is visible under the unconfigured filter', () => {
    const rule = createRule()
    const filters: EnhancementRuleFilters = { rule_status_filter: 'unconfigured' }

    expect(ruleHiddenReason(rule, filters)).toBeNull()
  })

  test('manual rule without AI suggestions is hidden by the pending filter', () => {
    const rule = createRule({ category_id: 'cat-1' })
    const filters: EnhancementRuleFilters = { rule_status_filter: 'pending' }

    expect(ruleHiddenReason(rule, filters)).toBe('the "Pending" filter')
  })

  test('rule is hidden when its category is not in the category filter', () => {
    const rule = createRule({ category_id: 'cat-1' })
    const filters: EnhancementRuleFilters = { category_ids: ['cat-2'] }

    expect(ruleHiddenReason(rule, filters)).toBe('the category filter')
  })

  test('rule is hidden when its counterparty is not in the counterparty filter', () => {
    const rule = createRule({ counterparty_account_id: 'acc-1' })
    const filters: EnhancementRuleFilters = { counterparty_account_ids: ['acc-2'] }

    expect(ruleHiddenReason(rule, filters)).toBe('the counterparty filter')
  })

  test('rule is hidden when its source does not match the source filter', () => {
    const rule = createRule({ source: EnhancementRuleSource.MANUAL })
    const filters: EnhancementRuleFilters = { source: EnhancementRuleSource.AUTO }

    expect(ruleHiddenReason(rule, filters)).toBe('the source filter')
  })

  test('rule is hidden when no pattern matches the match-type filter', () => {
    const rule = createRule({
      patterns: [{ id: 'p1', normalized_description: 'x', match_type: MatchType.INFIX, sort_order: 0 }],
    })
    const filters: EnhancementRuleFilters = { match_type: MatchType.EXACT }

    expect(ruleHiddenReason(rule, filters)).toBe('the match-type filter')
  })

  test('rule is hidden when no pattern matches the description search', () => {
    const rule = createRule()
    const filters: EnhancementRuleFilters = { description_search: 'netflix' }

    expect(ruleHiddenReason(rule, filters)).toBe('the description search')
  })

  test('rule is visible when a pattern contains the description search', () => {
    const rule = createRule()
    const filters: EnhancementRuleFilters = { description_search: 'POCKET' }

    expect(ruleHiddenReason(rule, filters)).toBeNull()
  })

  test('no filters means never hidden', () => {
    const rule = createRule({ category_id: 'cat-1', counterparty_account_id: 'acc-1' })

    expect(ruleHiddenReason(rule, {})).toBeNull()
  })
})
