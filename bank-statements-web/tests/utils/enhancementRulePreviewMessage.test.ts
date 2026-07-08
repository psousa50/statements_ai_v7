import { expect, test, describe } from 'vitest'
import { buildPreviewMessage } from '@/utils/enhancementRulePreviewMessage'

const base = { isEditing: true, applyToExisting: false, hasAction: true }

describe('buildPreviewMessage', () => {
  test('no matches at all', () => {
    const msg = buildPreviewMessage({ ...base, matchCount: 0, wouldUpdate: 0 })
    expect(msg.severity).toBe('info')
    expect(msg.primary).toContain('No existing transactions match')
    expect(msg.secondary).toContain('future transactions')
  })

  test('matches but nothing would change because already up to date', () => {
    const msg = buildPreviewMessage({ ...base, matchCount: 806, wouldUpdate: 0, hasAction: true })
    expect(msg.primary).toContain('806 existing transactions match')
    expect(msg.secondary).toBe('None would be updated — they are already up to date.')
  })

  test('matches but rule has no category or counterparty', () => {
    const msg = buildPreviewMessage({ ...base, matchCount: 806, wouldUpdate: 0, hasAction: false })
    expect(msg.secondary).toContain('add a category or counterparty')
  })

  test('editing and applying now warns and states what will be updated', () => {
    const msg = buildPreviewMessage({
      matchCount: 806,
      wouldUpdate: 800,
      isEditing: true,
      applyToExisting: true,
      hasAction: true,
    })
    expect(msg.severity).toBe('warning')
    expect(msg.primary).toContain('806 existing transactions match')
    expect(msg.secondary).toContain('800 will be updated when you save')
  })

  test('editing without applying is conditional', () => {
    const msg = buildPreviewMessage({
      matchCount: 10,
      wouldUpdate: 4,
      isEditing: true,
      applyToExisting: false,
      hasAction: true,
    })
    expect(msg.severity).toBe('info')
    expect(msg.secondary).toBe('4 would be updated if you apply this rule to existing transactions.')
  })

  test('singular grammar for a single match', () => {
    const msg = buildPreviewMessage({ ...base, matchCount: 1, wouldUpdate: 1 })
    expect(msg.primary).toContain('1 existing transaction matches this pattern')
  })
})
