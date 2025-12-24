import { useState, useEffect } from 'react'
import { useRecurringPatterns } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { RecurringPatternsTable } from '../components/RecurringPatternsTable'
import { RecurringExpensesCharts } from '../components/RecurringExpensesCharts'
import './RecurringExpensesPage.css'

type TabType = 'transactions' | 'charts'

export const RecurringExpensesPage = () => {
  const [activeOnly, setActiveOnly] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('transactions')

  const { recurringPatterns, loading, error, fetchRecurringPatterns } = useRecurringPatterns()
  const { categories } = useCategories()

  useEffect(() => {
    fetchRecurringPatterns(activeOnly)
  }, [activeOnly, fetchRecurringPatterns])

  return (
    <div className="recurring-expenses-page">
      <header className="page-header">
        <div className="header-content">
          <div>
            <h1>Recurring Expenses</h1>
            <p className="page-description">Monthly recurring expenses detected from the last 12 months</p>
          </div>
          <div className="header-controls">
            <label className="toggle-label">
              <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
              <span>Active only</span>
            </label>
          </div>
        </div>
      </header>

      <div className="tabs-container">
        <button
          className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('transactions')}
        >
          Transactions
        </button>
        <button
          className={`tab-button ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Charts
        </button>
      </div>

      <main className="page-content">
        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-indicator">Loading recurring patterns...</div>
        ) : recurringPatterns && recurringPatterns.patterns.length > 0 ? (
          activeTab === 'transactions' ? (
            <RecurringPatternsTable
              patterns={recurringPatterns.patterns}
              categories={categories || []}
              totalMonthlyRecurring={recurringPatterns.summary.total_monthly_recurring}
              onRefresh={() => fetchRecurringPatterns(activeOnly)}
            />
          ) : (
            <RecurringExpensesCharts
              patterns={recurringPatterns.patterns}
              categories={categories || []}
              totalMonthlyRecurring={recurringPatterns.summary.total_monthly_recurring}
            />
          )
        ) : (
          <div className="no-data-message">No recurring expense patterns found.</div>
        )}
      </main>
    </div>
  )
}
