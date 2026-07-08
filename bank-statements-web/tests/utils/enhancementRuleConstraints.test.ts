import { expect, test, describe } from 'vitest'
import { hasRuleConstraints } from '@/utils/enhancementRuleConstraints'

describe('hasRuleConstraints', () => {
  test('no constraints at all', () => {
    expect(hasRuleConstraints({})).toBe(false)
  })

  test('null amounts and dates are not constraints (rule loaded from API)', () => {
    expect(hasRuleConstraints({ displayMinAmount: null, displayMaxAmount: null, startDate: null, endDate: null })).toBe(
      false
    )
  })

  test('undefined amounts and dates are not constraints', () => {
    expect(
      hasRuleConstraints({
        displayMinAmount: undefined,
        displayMaxAmount: undefined,
        startDate: undefined,
        endDate: undefined,
      })
    ).toBe(false)
  })

  test('a zero minimum amount counts as a constraint', () => {
    expect(hasRuleConstraints({ displayMinAmount: 0 })).toBe(true)
  })

  test('a maximum amount counts as a constraint', () => {
    expect(hasRuleConstraints({ displayMaxAmount: 100 })).toBe(true)
  })

  test('a start date counts as a constraint', () => {
    expect(hasRuleConstraints({ startDate: '2024-01-01' })).toBe(true)
  })

  test('an end date counts as a constraint', () => {
    expect(hasRuleConstraints({ endDate: '2024-12-31' })).toBe(true)
  })
})
