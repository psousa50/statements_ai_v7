export function hasRuleConstraints(args: {
  displayMinAmount?: number | null
  displayMaxAmount?: number | null
  startDate?: string | null
  endDate?: string | null
}): boolean {
  const { displayMinAmount, displayMaxAmount, startDate, endDate } = args
  return typeof displayMinAmount === 'number' || typeof displayMaxAmount === 'number' || !!startDate || !!endDate
}
