import { useState, useMemo } from 'react'
import { RecurringPattern } from '../api/TransactionClient'
import { Category } from '../types/Transaction'
import { useApi } from '../api/ApiContext'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'
import MergeIcon from '@mui/icons-material/MergeType'
import VisibilityIcon from '@mui/icons-material/Visibility'

type SortField = 'description' | 'category' | 'average_amount' | 'total_annual_cost' | 'transaction_count'
type SortDirection = 'asc' | 'desc'

interface RecurringPatternsTableProps {
  patterns: RecurringPattern[]
  categories: Category[]
  totalMonthlyRecurring: number
  onRefresh?: () => void
}

export const RecurringPatternsTable = ({
  patterns,
  categories,
  totalMonthlyRecurring,
  onRefresh,
}: RecurringPatternsTableProps) => {
  const api = useApi()
  const [sortField, setSortField] = useState<SortField>('average_amount')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [mergeModalOpen, setMergeModalOpen] = useState(false)
  const [patternToMerge, setPatternToMerge] = useState<RecurringPattern | null>(null)
  const [selectedTargetPattern, setSelectedTargetPattern] = useState<string>('')
  const [merging, setMerging] = useState(false)
  const [mergeError, setMergeError] = useState<string | null>(null)

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

  const TRANSACTION_IDS_URL_THRESHOLD = 50

  const handleViewTransactions = async (pattern: RecurringPattern) => {
    const params = new URLSearchParams()
    params.set('exclude_transfers', 'false')
    params.set('pattern_label', pattern.description)

    if (pattern.transaction_ids.length <= TRANSACTION_IDS_URL_THRESHOLD) {
      params.set('transaction_ids', pattern.transaction_ids.join(','))
    } else {
      const savedFilter = await api.transactions.createSavedFilter(pattern.transaction_ids)
      params.set('saved_filter_id', savedFilter.id)
    }

    window.open(`/transactions?${params.toString()}`, '_blank')
  }

  const handleMergeClick = (pattern: RecurringPattern) => {
    setPatternToMerge(pattern)
    setSelectedTargetPattern('')
    setMergeError(null)
    setMergeModalOpen(true)
  }

  const handleMergeConfirm = async () => {
    if (!patternToMerge || !selectedTargetPattern) return

    setMerging(true)
    setMergeError(null)

    try {
      await api.descriptionGroups.create({
        name: `Merged: ${patternToMerge.description}`,
        normalized_descriptions: [patternToMerge.normalized_description, selectedTargetPattern],
      })

      setMergeModalOpen(false)
      setPatternToMerge(null)
      setSelectedTargetPattern('')

      if (onRefresh) {
        onRefresh()
      }
    } catch (error) {
      console.error('Error merging patterns:', error)
      setMergeError('Failed to merge patterns. Please try again.')
    } finally {
      setMerging(false)
    }
  }

  const handleMergeCancel = () => {
    setMergeModalOpen(false)
    setPatternToMerge(null)
    setSelectedTargetPattern('')
    setMergeError(null)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }

  const SortableHeader = ({
    field,
    children,
    align,
  }: {
    field: SortField
    children: React.ReactNode
    align?: 'left' | 'right'
  }) => {
    const isActive = sortField === field
    const direction = isActive ? sortDirection : undefined

    return (
      <th
        className={`sortable-header ${isActive ? 'active' : ''}`}
        onClick={() => handleSort(field)}
        style={align ? { textAlign: align } : undefined}
      >
        <div className="header-content" style={align === 'right' ? { justifyContent: 'flex-end' } : undefined}>
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
              <SortableHeader field="average_amount" align="right">Monthly Amount</SortableHeader>
              <SortableHeader field="total_annual_cost" align="right">Annual Cost</SortableHeader>
              <SortableHeader field="transaction_count" align="right">Occurrences</SortableHeader>
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
                    <div className="actions-cell">
                      <button
                        className="view-btn"
                        onClick={() => handleViewTransactions(pattern)}
                        title="View transactions"
                      >
                        <VisibilityIcon fontSize="small" />
                      </button>
                      <button
                        className="merge-btn"
                        onClick={() => handleMergeClick(pattern)}
                        title="Merge with another pattern"
                      >
                        <MergeIcon fontSize="small" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {mergeModalOpen && patternToMerge && (
        <div className="merge-modal-overlay" onClick={handleMergeCancel}>
          <div className="merge-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Merge Recurring Pattern</h3>
            <p className="modal-description">
              Merge "<strong>{patternToMerge.description}</strong>" with:
            </p>

            {mergeError && <div className="error-message">{mergeError}</div>}

            <div className="pattern-selector">
              {sortedPatterns
                .filter((p) => p.normalized_description !== patternToMerge.normalized_description)
                .map((pattern) => (
                  <label key={pattern.normalized_description} className="pattern-option">
                    <input
                      type="radio"
                      name="target-pattern"
                      value={pattern.normalized_description}
                      checked={selectedTargetPattern === pattern.normalized_description}
                      onChange={(e) => setSelectedTargetPattern(e.target.value)}
                    />
                    <div className="pattern-option-content">
                      <div className="pattern-option-description">{pattern.description}</div>
                      <div className="pattern-option-details">
                        {pattern.transaction_count} transactions • {formatCurrency(pattern.average_amount)}/month
                      </div>
                    </div>
                  </label>
                ))}
            </div>

            <div className="modal-actions">
              <button className="cancel-btn" onClick={handleMergeCancel} disabled={merging}>
                Cancel
              </button>
              <button className="confirm-btn" onClick={handleMergeConfirm} disabled={!selectedTargetPattern || merging}>
                {merging ? 'Merging...' : 'Merge'}
              </button>
            </div>
          </div>
        </div>
      )}

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
          border-bottom: 2px solid var(--border-primary);
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
          color: var(--button-primary);
        }

        .recurring-patterns-table td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-primary);
        }

        .recurring-patterns-table tbody tr {
          background: var(--bg-primary);
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
          background: #fef3c7;
          color: #92400e;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }

        .amount-cell {
          text-align: right;
          font-weight: 500;
        }

        .count-cell {
          text-align: right;
        }

        .date-cell {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .view-btn {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border-primary);
          padding: 6px 8px;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: all 0.2s;
        }

        .view-btn:hover {
          background: var(--bg-hover);
          border-color: var(--button-primary);
          color: var(--button-primary);
        }

        .empty-state {
          text-align: center;
          padding: 48px 16px;
          color: var(--text-secondary);
        }

        .actions-cell {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .merge-btn {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border-primary);
          padding: 6px 8px;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: all 0.2s;
        }

        .merge-btn:hover {
          background: var(--bg-hover);
          border-color: var(--button-primary);
          color: var(--button-primary);
        }

        .merge-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .merge-modal {
          background: var(--bg-primary);
          border-radius: 8px;
          padding: 24px;
          max-width: 600px;
          width: 90%;
          max-height: 80vh;
          overflow: auto;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .merge-modal h3 {
          margin: 0 0 16px 0;
          font-size: 20px;
          font-weight: 600;
        }

        .modal-description {
          margin: 0 0 20px 0;
          color: var(--text-secondary);
        }

        .error-message {
          background: var(--negative-amount-bg);
          color: var(--negative-amount);
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 16px;
        }

        .pattern-selector {
          max-height: 400px;
          overflow-y: auto;
          margin-bottom: 24px;
          border: 1px solid var(--border-primary);
          border-radius: 4px;
        }

        .pattern-option {
          display: flex;
          align-items: flex-start;
          padding: 12px;
          border-bottom: 1px solid var(--border-primary);
          cursor: pointer;
          transition: background 0.2s;
        }

        .pattern-option:last-child {
          border-bottom: none;
        }

        .pattern-option:hover {
          background: var(--bg-hover);
        }

        .pattern-option input[type="radio"] {
          margin-right: 12px;
          margin-top: 2px;
          cursor: pointer;
        }

        .pattern-option-content {
          flex: 1;
        }

        .pattern-option-description {
          font-weight: 500;
          margin-bottom: 4px;
        }

        .pattern-option-details {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
        }

        .cancel-btn,
        .confirm-btn {
          padding: 8px 16px;
          border-radius: 4px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .cancel-btn {
          background: var(--bg-secondary);
          color: var(--text-primary);
          border: 1px solid var(--border-primary);
        }

        .cancel-btn:hover:not(:disabled) {
          background: var(--bg-hover);
        }

        .confirm-btn {
          background: var(--button-primary);
          color: white;
          border: none;
        }

        .confirm-btn:hover:not(:disabled) {
          background: var(--button-primary-hover);
        }

        .confirm-btn:disabled,
        .cancel-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  )
}
