import { format } from 'date-fns'
import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Category, Transaction, Source } from '../types/Transaction'

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  sources: Source[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => void
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

export const TransactionTable = ({
  transactions,
  categories,
  sources,
  loading,
  onCategorize,
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
  const getSourceName = (sourceId?: string) => {
    if (!sourceId) return 'Unknown'
    const source = sources.find((s) => s.id === sourceId)
    return source ? source.name : 'Unknown'
  }

  return (
    <div className="transaction-table">
      <h2>Transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Source</th>
            {onCategorize && <th>Category</th>}
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{formatDate(transaction.date)}</td>
              <td>{transaction.description}</td>
              <td className={transaction.amount < 0 ? 'negative' : 'positive'}>{formatAmount(transaction.amount)}</td>
              <td>{getSourceName(transaction.source_id)}</td>
              {onCategorize && (
                <td>
                  <CategoryPicker transaction={transaction} categories={categories} onCategorize={onCategorize} />
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
