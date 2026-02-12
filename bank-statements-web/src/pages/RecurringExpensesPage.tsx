import { useState, useEffect, useMemo } from 'react'
import { useRecurringPatterns } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { RecurringPatternsTable } from '../components/RecurringPatternsTable'
import { RecurringExpensesCharts } from '../components/RecurringExpensesCharts'
import './RecurringExpensesPage.css'

type ViewTab = 'transactions' | 'charts'
type PatternType = 'monthly' | 'quarterly' | 'yearly'

const PATTERN_LABELS: Record<PatternType, string> = {
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  yearly: 'Yearly',
}

export const RecurringExpensesPage = () => {
  const [activeOnly, setActiveOnly] = useState(true)
  const [viewTab, setViewTab] = useState<ViewTab>('transactions')
  const [patternType, setPatternType] = useState<PatternType>('monthly')

  const { recurringPatterns, loading, error, fetchRecurringPatterns } = useRecurringPatterns()
  const { categories } = useCategories()

  useEffect(() => {
    fetchRecurringPatterns(activeOnly)
  }, [activeOnly, fetchRecurringPatterns])

  const filteredPatterns = useMemo(() => {
    if (!recurringPatterns) return []
    return recurringPatterns.patterns.filter((p) => p.pattern_type === patternType)
  }, [recurringPatterns, patternType])

  const currentTotal = useMemo(() => {
    if (!recurringPatterns) return 0
    switch (patternType) {
      case 'monthly':
        return recurringPatterns.summary.total_monthly_recurring
      case 'quarterly':
        return recurringPatterns.summary.total_quarterly_recurring
      case 'yearly':
        return recurringPatterns.summary.total_yearly_recurring
    }
  }, [recurringPatterns, patternType])

  const monthlyCount = recurringPatterns?.summary.monthly_pattern_count ?? 0
  const quarterlyCount = recurringPatterns?.summary.quarterly_pattern_count ?? 0
  const yearlyCount = recurringPatterns?.summary.yearly_pattern_count ?? 0

  return (
    <div className="recurring-expenses-page">
      <header className="page-header">
        <div className="header-content">
          <div>
            <h1>Recurring Expenses</h1>
            <p className="page-description">
              {PATTERN_LABELS[patternType]} recurring expenses detected from your transaction history
            </p>
          </div>
          <div className="header-controls">
            <label className="toggle-label">
              <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
              <span>Active only</span>
            </label>
          </div>
        </div>
      </header>

      <div className="tabs-row">
        <div className="tabs-container pattern-type-tabs">
          <button
            className={`tab-button ${patternType === 'monthly' ? 'active' : ''}`}
            onClick={() => setPatternType('monthly')}
          >
            Monthly ({monthlyCount})
          </button>
          <button
            className={`tab-button ${patternType === 'quarterly' ? 'active' : ''}`}
            onClick={() => setPatternType('quarterly')}
          >
            Quarterly ({quarterlyCount})
          </button>
          <button
            className={`tab-button ${patternType === 'yearly' ? 'active' : ''}`}
            onClick={() => setPatternType('yearly')}
          >
            Yearly ({yearlyCount})
          </button>
        </div>

        <div className="tabs-container view-tabs">
          <button
            className={`tab-button ${viewTab === 'transactions' ? 'active' : ''}`}
            onClick={() => setViewTab('transactions')}
          >
            Transactions
          </button>
          <button className={`tab-button ${viewTab === 'charts' ? 'active' : ''}`} onClick={() => setViewTab('charts')}>
            Charts
          </button>
        </div>
      </div>

      <main className="page-content">
        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-indicator">Loading recurring patterns...</div>
        ) : filteredPatterns.length > 0 ? (
          viewTab === 'transactions' ? (
            <RecurringPatternsTable
              patterns={filteredPatterns}
              categories={categories || []}
              totalMonthlyRecurring={currentTotal}
              patternType={patternType}
              onRefresh={() => fetchRecurringPatterns(activeOnly)}
            />
          ) : (
            <RecurringExpensesCharts
              patterns={filteredPatterns}
              categories={categories || []}
              totalMonthlyRecurring={currentTotal}
              patternType={patternType}
            />
          )
        ) : (
          <div className="no-data-message">No {patternType} recurring expense patterns found.</div>
        )}
      </main>
    </div>
  )
}
