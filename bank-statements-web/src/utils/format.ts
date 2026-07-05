export function formatCurrency(amount: number, currency = 'EUR', maximumFractionDigits = 2): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency,
    maximumFractionDigits,
    minimumFractionDigits: Math.min(2, maximumFractionDigits),
  }).format(amount)
}
