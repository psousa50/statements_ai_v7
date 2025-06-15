import React, { useState } from 'react'
import { Category } from '../types/Transaction'
import { TransactionCategorization, CategorizationSource, SortField, SortDirection } from '../types/TransactionCategorization'

interface TransactionCategorizationTableProps {
  categorizations: TransactionCategorization[]
  categories: Category[]
  loading: boolean
  sortField?: SortField
  sortDirection?: SortDirection
  onEdit?: (categorization: TransactionCategorization) => void
  onDelete?: (id: string) => void
  onViewTransactions?: (description: string) => void
  onSort?: (field: SortField) => void
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

const getSourceBadge = (source: CategorizationSource): JSX.Element => {
  const isManual = source === CategorizationSource.MANUAL
  return <span className={`source-badge ${isManual ? 'manual' : 'ai'}`}>{isManual ? '👤 Manual' : '🤖 AI'}</span>
}

const getCategoryHierarchy = (category: Category | undefined, categories: Category[]): string => {
  if (!category) return 'Unknown'

  if (category.parent_id) {
    const parent = categories.find((cat) => cat.id === category.parent_id)
    if (parent) {
      return `${parent.name} > ${category.name}`
    }
  }

  return category.name
}

const getUsageIndicator = (transactionCount?: number): JSX.Element => {
  if (!transactionCount || transactionCount === 0) {
    return <span className="usage-indicator unused">🔴 Unused</span>
  } else if (transactionCount >= 50) {
    return <span className="usage-indicator high">🟢 High ({transactionCount})</span>
  } else if (transactionCount >= 10) {
    return <span className="usage-indicator medium">🟡 Medium ({transactionCount})</span>
  } else {
    return <span className="usage-indicator low">🟠 Low ({transactionCount})</span>
  }
}

const SortableHeader = ({ 
  field, 
  children, 
  currentSortField, 
  currentSortDirection, 
  onSort 
}: { 
  field: SortField
  children: React.ReactNode
  currentSortField?: SortField
  currentSortDirection?: SortDirection
  onSort?: (field: SortField) => void
}) => {
  const isActive = currentSortField === field
  const direction = isActive ? currentSortDirection : undefined
  
  return (
    <th 
      className={`sortable-header ${isActive ? 'active' : ''}`}
      onClick={() => onSort?.(field)}
      style={{ cursor: onSort ? 'pointer' : 'default' }}
    >
      <div className="header-content">
        <span>{children}</span>
        {onSort && (
          <span className="sort-indicator">
            {isActive && direction === 'asc' && '↑'}
            {isActive && direction === 'desc' && '↓'}
            {!isActive && '⇅'}
          </span>
        )}
      </div>
    </th>
  )
}

export const TransactionCategorizationTable = ({
  categorizations,
  categories,
  loading,
  sortField,
  sortDirection,
  onEdit,
  onDelete,
  onViewTransactions,
  onSort,
}: TransactionCategorizationTableProps) => {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const toggleRowExpansion = (id: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRows(newExpanded)
  }

  if (loading) {
    return (
      <div className="table-loading">
        <div className="loading-spinner"></div>
        <p>Loading categorization rules...</p>
      </div>
    )
  }

  if (categorizations.length === 0) {
    return (
      <div className="table-empty">
        <p>No categorization rules found.</p>
        <p>
          Rules will be automatically created when transactions are categorized by AI, or you can create them manually.
        </p>
      </div>
    )
  }

  return (
    <div className="categorization-table-container">
      <table className="categorization-table">
        <thead>
          <tr>
            <SortableHeader
              field="normalized_description"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Description
            </SortableHeader>
            <SortableHeader
              field="category"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Category
            </SortableHeader>
            <SortableHeader
              field="usage"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Usage
            </SortableHeader>
            <SortableHeader
              field="source"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Source
            </SortableHeader>
            <SortableHeader
              field="created_at"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Created
            </SortableHeader>
            <th className="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          {categorizations.map((categorization) => (
            <React.Fragment key={categorization.id}>
              <tr
                className={`categorization-row ${expandedRows.has(categorization.id) ? 'expanded' : ''}`}
                onClick={() => toggleRowExpansion(categorization.id)}
              >
                <td className="col-description">
                  <span className="description-text">{categorization.normalized_description}</span>
                </td>
                <td className="col-category">{getCategoryHierarchy(categorization.category, categories)}</td>
                <td className="col-usage">{getUsageIndicator(categorization.transaction_count)}</td>
                <td className="col-source">{getSourceBadge(categorization.source)}</td>
                <td className="col-created">{formatDate(categorization.created_at)}</td>
                <td className="col-actions">
                  <div className="action-buttons">
                    {onViewTransactions && (
                      <button
                        className="action-button view-transactions"
                        onClick={(e) => {
                          e.stopPropagation()
                          onViewTransactions(categorization.normalized_description)
                        }}
                        title="View matching transactions"
                      >
                        🔍
                      </button>
                    )}
                    {onEdit && (
                      <button
                        className="action-button edit"
                        onClick={(e) => {
                          e.stopPropagation()
                          onEdit(categorization)
                        }}
                        title="Edit rule"
                      >
                        ✏️
                      </button>
                    )}
                    {onDelete && (
                      <button
                        className="action-button delete"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (window.confirm('Are you sure you want to delete this categorization rule?')) {
                            onDelete(categorization.id)
                          }
                        }}
                        title="Delete rule"
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </td>
              </tr>
              {expandedRows.has(categorization.id) && (
                <tr className="expanded-row">
                  <td colSpan={6}>
                    <div className="expanded-content">
                      <div className="expanded-details">
                        <div className="detail-row">
                          <strong>Full Description:</strong> {categorization.normalized_description}
                        </div>
                        <div className="detail-row">
                          <strong>Category ID:</strong> {categorization.category_id}
                        </div>
                        <div className="detail-row">
                          <strong>Last Updated:</strong> {formatDate(categorization.updated_at)}
                        </div>
                        {categorization.transaction_count !== undefined && (
                          <div className="detail-row">
                            <strong>Transaction Matches:</strong> {categorization.transaction_count} transactions use
                            this rule
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
