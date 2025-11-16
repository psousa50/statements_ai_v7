import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { RecurringPattern } from '../api/TransactionClient'
import { Category } from '../types/Transaction'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'

type SortField = 'description' | 'category' | 'average_amount' | 'total_annual_cost' | 'transaction_count'
type SortDirection = 'asc' | 'desc'

interface RecurringPatternsTableProps {
  patterns: RecurringPattern[]
  categories: Category[]
  totalMonthlyRecurring: number
}

export const RecurringPatternsTable = ({
  patterns,
  categories,
  totalMonthlyRecurring,
}: RecurringPatternsTableProps) => {
  const navigate = useNavigate()
  const [sortField, setSortField] = useState<SortField>('average_amount')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const getCategoryName = (categoryId?: string) => {
    if (!categoryId) return '-'
    const category = categories.find((c) => c.id === categoryId)
    return category?.name || '-'
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection(field === 'description' || field === 'category' ? 'asc' : 'desc')
    }
  }

  const sortedPatterns = useMemo(() => {
    const getCategoryNameForSort = (categoryId?: string) => {
      if (!categoryId) return '-'
      const category = categories.find((c) => c.id === categoryId)
      return category?.name || '-'
    }

    const sorted = [...patterns].sort((a, b) => {
      let aValue: string | number
      let bValue: string | number

      switch (sortField) {
        case 'description':
          aValue = a.description.toLowerCase()
          bValue = b.description.toLowerCase()
          break
        case 'category':
          aValue = getCategoryNameForSort(a.category_id).toLowerCase()
          bValue = getCategoryNameForSort(b.category_id).toLowerCase()
          break
        case 'average_amount':
          aValue = a.average_amount
          bValue = b.average_amount
          break
        case 'total_annual_cost':
          aValue = a.total_annual_cost
          bValue = b.total_annual_cost
          break
        case 'transaction_count':
          aValue = a.transaction_count
          bValue = b.transaction_count
          break
        default:
          return 0
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
      return 0
    })

    return sorted
  }, [patterns, sortField, sortDirection, categories])

  const handleViewTransactions = (pattern: RecurringPattern) => {
    const params = new URLSearchParams()
    params.set('description_search', pattern.normalized_description)
    navigate(`/transactions?${params.toString()}`)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => {
    const isActive = sortField === field
    const direction = isActive ? sortDirection : undefined

    return (
      <th className={`sortable-header ${isActive ? 'active' : ''}`} onClick={() => handleSort(field)}>
        <div className="header-content">
          <span>{children}</span>
          <span className="sort-indicator">
            {!isActive && <UnfoldMoreIcon fontSize="small" />}
            {isActive && direction === 'asc' && <ArrowUpwardIcon fontSize="small" />}
            {isActive && direction === 'desc' && <ArrowDownwardIcon fontSize="small" />}
          </span>
        </div>
      </th>
    )
  }

  return (
    <div className="recurring-patterns-container">
      <div className="recurring-patterns-summary">
        <h3>Summary</h3>
        <div className="summary-stats">
          <div className="stat-card">
            <span className="stat-label">Total Monthly Recurring</span>
            <span className="stat-value">{formatCurrency(totalMonthlyRecurring)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Number of Patterns</span>
            <span className="stat-value">{patterns.length}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Annual Cost</span>
            <span className="stat-value">{formatCurrency(totalMonthlyRecurring * 12)}</span>
          </div>
        </div>
      </div>

      <div className="recurring-patterns-table-container">
        <table className="recurring-patterns-table">
          <thead>
            <tr>
              <SortableHeader field="description">Description</SortableHeader>
              <SortableHeader field="category">Category</SortableHeader>
              <th>Frequency</th>
              <SortableHeader field="average_amount">Monthly Amount</SortableHeader>
              <SortableHeader field="total_annual_cost">Annual Cost</SortableHeader>
              <SortableHeader field="transaction_count">Occurrences</SortableHeader>
              <th>First/Last Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedPatterns.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-state">
                  No recurring patterns found with the current filters.
                </td>
              </tr>
            ) : (
              sortedPatterns.map((pattern, index) => (
                <tr key={index}>
                  <td>
                    <div className="pattern-description">
                      <strong>{pattern.description}</strong>
                      {pattern.amount_variance > 0.05 && (
                        <span className="variance-badge" title="Amount varies">
                          ±{(pattern.amount_variance * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </td>
                  <td>{getCategoryName(pattern.category_id)}</td>
                  <td>
                    <span className="frequency-badge">{pattern.frequency}</span>
                  </td>
                  <td className="amount-cell">{formatCurrency(pattern.average_amount)}</td>
                  <td className="amount-cell">{formatCurrency(pattern.total_annual_cost)}</td>
                  <td className="count-cell">{pattern.transaction_count}</td>
                  <td className="date-cell">
                    <div>
                      {formatDate(pattern.first_transaction_date)}
                      <br />
                      {formatDate(pattern.last_transaction_date)}
                    </div>
                  </td>
                  <td>
                    <button className="view-transactions-btn" onClick={() => handleViewTransactions(pattern)}>
                      View Transactions
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <style>{`
        .recurring-patterns-container {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .recurring-patterns-summary {
          background: var(--bg-secondary);
          border-radius: 8px;
          padding: 20px;
        }

        .recurring-patterns-summary h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .summary-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .stat-card {
          background: var(--bg-primary);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .recurring-patterns-table-container {
          overflow-x: auto;
        }

        .recurring-patterns-table {
          width: 100%;
          border-collapse: collapse;
          background: var(--bg-secondary);
          border-radius: 8px;
          overflow: hidden;
        }

        .recurring-patterns-table th {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          font-weight: 600;
          text-align: left;
          padding: 12px 16px;
          border-bottom: 2px solid var(--border-color);
        }

        .sortable-header {
          cursor: pointer;
          user-select: none;
          transition: background 0.2s;
        }

        .sortable-header:hover {
          background: var(--bg-hover);
        }

        .sortable-header .header-content {
          display: flex;
          align-items: center;
          gap: 8px;
          justify-content: space-between;
        }

        .sortable-header .sort-indicator {
          display: flex;
          align-items: center;
          color: var(--text-secondary);
          opacity: 0.5;
        }

        .sortable-header.active .sort-indicator {
          opacity: 1;
          color: var(--primary-color);
        }

        .recurring-patterns-table td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color);
        }

        .recurring-patterns-table tbody tr:hover {
          background: var(--bg-hover);
        }

        .pattern-description {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .variance-badge {
          background: var(--warning-bg);
          color: var(--warning-text);
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }

        .frequency-badge {
          background: var(--primary-bg);
          color: var(--primary-text);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
        }

        .amount-cell {
          text-align: right;
          font-weight: 500;
        }

        .count-cell {
          text-align: center;
        }

        .date-cell {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .view-transactions-btn {
          background: var(--primary-color);
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          transition: background 0.2s;
        }

        .view-transactions-btn:hover {
          background: var(--primary-hover);
        }

        .empty-state {
          text-align: center;
          padding: 48px 16px;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  )
}
