export interface PreviewMessage {
  severity: 'info' | 'warning'
  primary: string
  secondary: string | null
}

const matchesLine = (matchCount: number): string =>
  `${matchCount} existing ${matchCount === 1 ? 'transaction matches' : 'transactions match'} this pattern.`

export function buildPreviewMessage(args: {
  matchCount: number
  wouldUpdate: number
  isEditing: boolean
  applyToExisting: boolean
  hasAction: boolean
}): PreviewMessage {
  const { matchCount, wouldUpdate, isEditing, applyToExisting, hasAction } = args

  if (matchCount === 0) {
    return {
      severity: 'info',
      primary: '📊 No existing transactions match this rule pattern.',
      secondary: 'This rule will only apply to future transactions.',
    }
  }

  if (wouldUpdate === 0) {
    return {
      severity: 'info',
      primary: `📊 ${matchesLine(matchCount)}`,
      secondary: hasAction
        ? 'None would be updated — they are already up to date.'
        : 'None would be updated — add a category or counterparty for this rule to change anything.',
    }
  }

  const applyingNow = isEditing && applyToExisting
  return {
    severity: applyingNow ? 'warning' : 'info',
    primary: `${applyingNow ? '⚠️' : '📊'} ${matchesLine(matchCount)}`,
    secondary: applyingNow
      ? `${wouldUpdate} will be updated when you save (manually categorised transactions are left untouched).`
      : `${wouldUpdate} would be updated if you apply this rule to existing transactions.`,
  }
}
