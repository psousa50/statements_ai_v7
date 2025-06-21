import { format } from 'date-fns'
import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Category, Transaction, Account } from '../types/Transaction'

export type TransactionSortField = 'date' | 'description' | 'amount' | 'created_at'
export type TransactionSortDirection = 'asc' | 'desc'

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  accounts: Account[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => void
  sortField?: TransactionSortField
  sortDirection?: TransactionSortDirection
  onSort?: (field: TransactionSortField) => void
  showRunningBalance?: boolean
}

interface CategoryPickerProps {
  transaction: Transaction
  categories: Category[]
  onCategorize: (transactionId: string, categoryId?: string) => void
}

const CategoryPicker = ({ transaction, categories, onCategorize }: CategoryPickerProps) => {
  const [input, setInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Get current category
  const currentCategory = useMemo(() => {
    return transaction.category_id ? categories.find((c) => c.id === transaction.category_id) : null
  }, [transaction.category_id, categories])

  // Filter categories based on input
  const filteredCategories = useMemo(() => {
    return categories.filter((category) => category.name.toLowerCase().includes(input.toLowerCase()))
  }, [categories, input])

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
        setInput('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCategorySelect = useCallback(
    (categoryId: string) => {
      onCategorize(transaction.id, categoryId)
      setInput('')
      setShowSuggestions(false)
    },
    [transaction.id, onCategorize]
  )

  const handleCategoryRemove = useCallback(() => {
    onCategorize(transaction.id, undefined)
  }, [transaction.id, onCategorize])

  const handleInputChange = useCallback(
    (value: string) => {
      setInput(value)
      setShowSuggestions(value.length > 0 && filteredCategories.length > 0)
    },
    [filteredCategories.length]
  )

  const handleInputKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && filteredCategories.length > 0) {
        e.preventDefault()
        handleCategorySelect(filteredCategories[0].id)
      } else if (e.key === 'Escape') {
        setShowSuggestions(false)
        setInput('')
      }
    },
    [filteredCategories, handleCategorySelect]
  )

  return (
    <div className="transaction-category-picker" ref={containerRef}>
      <div className="category-picker-container">
        {currentCategory ? (
          <span className="current-category-tag">
            {currentCategory.name}
            <button onClick={handleCategoryRemove} className="category-remove-btn" type="button">
              ×
            </button>
          </span>
        ) : (
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleInputKeyDown}
            onFocus={() => setShowSuggestions(input.length > 0 && filteredCategories.length > 0)}
            placeholder="Search category..."
            className="category-picker-input"
          />
        )}
      </div>

      {showSuggestions && filteredCategories.length > 0 && (
        <div className="category-picker-suggestions">
          {filteredCategories.slice(0, 6).map((category) => (
            <button
              key={category.id}
              onClick={() => handleCategorySelect(category.id)}
              className="category-picker-suggestion"
              type="button"
            >
              {category.parent_id && '  └ '}
              {category.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const SortableHeader = ({
  field,
  children,
  currentSortField,
  currentSortDirection,
  onSort,
  className,
}: {
  field: TransactionSortField
  children: React.ReactNode
  currentSortField?: TransactionSortField
  currentSortDirection?: TransactionSortDirection
  onSort?: (field: TransactionSortField) => void
  className?: string
}) => {
  const isActive = currentSortField === field
  const direction = isActive ? currentSortDirection : undefined

  return (
    <th
      className={`sortable-header ${isActive ? 'active' : ''} ${className || ''}`}
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

export const TransactionTable = ({
  transactions,
  categories,
  accounts,
  loading,
  onCategorize,
  sortField,
  sortDirection,
  onSort,
  showRunningBalance = false,
}: TransactionTableProps) => {
  if (loading) {
    return <div className="loading">Loading transactions...</div>
  }

  if (transactions.length === 0) {
    return <div className="no-data">No transactions found. Add one to get started!</div>
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy')
    } catch (_error) {
      return dateString
    }
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  // Helper function to get source name by ID
  const getAccountName = (accountId?: string) => {
    if (!accountId) return 'Unknown'
    const account = accounts.find((a) => a.id === accountId)
    return account ? account.name : 'Unknown'
  }

  return (
    <div className="transaction-table">
      <h2>Transactions</h2>
      <table>
        <colgroup>
          <col style={{ width: '15%' }} />
          <col style={{ width: '35%' }} />
          {onCategorize && <col style={{ width: '20%' }} />}
          <col style={{ width: '15%' }} />
          <col style={{ width: '15%' }} />
        </colgroup>
        <thead>
          <tr>
            <SortableHeader
              field="date"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Date
            </SortableHeader>
            <SortableHeader
              field="description"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
            >
              Description
            </SortableHeader>
            {onCategorize && <th style={{ textAlign: 'left' }}>Category</th>}
            <SortableHeader
              field="amount"
              currentSortField={sortField}
              currentSortDirection={sortDirection}
              onSort={onSort}
              className="text-right"
            >
              Amount
            </SortableHeader>
            {showRunningBalance ? (
              <th className="text-right">Running Balance</th>
            ) : (
              <th style={{ textAlign: 'left' }}>Source</th>
            )}
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{formatDate(transaction.date)}</td>
              <td>{transaction.description}</td>
              {onCategorize && (
                <td>
                  <CategoryPicker transaction={transaction} categories={categories} onCategorize={onCategorize} />
                </td>
              )}
              <td className={`text-right ${transaction.amount < 0 ? 'negative' : 'positive'}`}>
                {formatAmount(transaction.amount)}
              </td>
              {showRunningBalance ? (
                <td className="running-balance text-right">
                  {transaction.running_balance !== undefined ? formatAmount(transaction.running_balance) : '-'}
                </td>
              ) : (
                <td>{getAccountName(transaction.account_id)}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
