import { format } from 'date-fns'
import { useState, useCallback, useEffect } from 'react'
import { Category, Transaction, Account } from '../types/Transaction'
import { Toast, ToastProps } from './Toast'
import { CategorySelector } from './CategorySelector'
import { useApi } from '../api/ApiContext'
import EditIcon from '@mui/icons-material/Edit'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import { ActionIconButton } from './ActionIconButton'

export type TransactionSortField = 'date' | 'description' | 'amount' | 'created_at'
export type TransactionSortDirection = 'asc' | 'desc'

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  accounts: Account[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => Promise<void>
  onEdit?: (transaction: Transaction) => void
  sortField?: TransactionSortField
  sortDirection?: TransactionSortDirection
  onSort?: (field: TransactionSortField) => void
  showRunningBalance?: boolean
}

interface CategoryCellProps {
  transaction: Transaction
  categories: Category[]
  onCategorize: (transactionId: string, categoryId?: string) => Promise<void>
  onShowToast: (toast: Omit<ToastProps, 'onClose'>) => void
  onCategoryCreated: (category: Category) => void
}

const CategoryCell = ({ transaction, categories, onCategorize, onShowToast, onCategoryCreated }: CategoryCellProps) => {
  const [isLoading, setIsLoading] = useState(false)
  const apiClient = useApi()

  const handleCategoryChange = useCallback(
    async (categoryId?: string) => {
      const previousCategoryId = transaction.category_id

      if (categoryId === previousCategoryId) {
        return
      }

      setIsLoading(true)
      try {
        await onCategorize(transaction.id, categoryId)

        if (!categoryId && previousCategoryId) {
          const categoryName = categories.find((c) => c.id === previousCategoryId)?.name || 'Category'
          onShowToast({
            message: `${categoryName} removed`,
            type: 'info',
            onUndo: async () => {
              try {
                await onCategorize(transaction.id, previousCategoryId)
              } catch (error) {
                console.error('Failed to restore category:', error)
                onShowToast({
                  message: 'Failed to restore category. Please try again.',
                  type: 'error',
                })
              }
            },
          })
        }
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        onShowToast({
          message: 'Failed to save category. Please try again.',
          type: 'error',
        })
      } finally {
        setIsLoading(false)
      }
    },
    [transaction.id, transaction.category_id, categories, onCategorize, onShowToast]
  )

  const handleCreateCategory = useCallback(
    async (name: string, parentId?: string) => {
      try {
        const newCategory = await apiClient.categories.create({ name, parent_id: parentId })
        onCategoryCreated(newCategory)
        return newCategory
      } catch (error) {
        console.error('Failed to create category:', error)
        onShowToast({
          message: 'Failed to create category. Please try again.',
          type: 'error',
        })
        return null
      }
    },
    [apiClient, onCategoryCreated, onShowToast]
  )

  if (isLoading) {
    return (
      <div className="category-picker-loading">
        <span>Saving...</span>
      </div>
    )
  }

  return (
    <CategorySelector
      categories={categories}
      selectedCategoryId={transaction.category_id}
      onCategoryChange={handleCategoryChange}
      placeholder="Select category..."
      allowClear={true}
      allowCreate={true}
      onCategoryCreate={handleCreateCategory}
    />
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
            {isActive && direction === 'asc' && <ArrowUpwardIcon sx={{ fontSize: '16px' }} />}
            {isActive && direction === 'desc' && <ArrowDownwardIcon sx={{ fontSize: '16px' }} />}
            {!isActive && <UnfoldMoreIcon sx={{ fontSize: '16px' }} />}
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
  onEdit,
  sortField,
  sortDirection,
  onSort,
  showRunningBalance = false,
}: TransactionTableProps) => {
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [localCategories, setLocalCategories] = useState<Category[]>(categories)

  useEffect(() => {
    setLocalCategories(categories)
  }, [categories])

  const handleShowToast = useCallback((toastProps: Omit<ToastProps, 'onClose'>) => {
    setToast(toastProps)
  }, [])

  const handleCategoryCreated = useCallback((newCategory: Category) => {
    setLocalCategories((prev) => [...prev, newCategory].sort((a, b) => a.name.localeCompare(b.name)))
  }, [])

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
          <col style={{ width: '30%' }} />
          {onCategorize && <col style={{ width: '20%' }} />}
          <col style={{ width: '15%' }} />
          <col style={{ width: '15%' }} />
          {onEdit && <col style={{ width: '5%' }} />}
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
            {onEdit && <th style={{ textAlign: 'center' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{formatDate(transaction.date)}</td>
              <td>
                <div className="transaction-description">
                  <div>{transaction.description}</div>
                  {transaction.counterparty_account_id && (
                    <div className={`counterparty-badge ${transaction.amount < 0 ? 'negative' : 'positive'}`}>
                      {transaction.amount < 0 ? 'to' : 'from'}: {getAccountName(transaction.counterparty_account_id)}
                    </div>
                  )}
                </div>
              </td>
              {onCategorize && (
                <td>
                  <CategoryCell
                    transaction={transaction}
                    categories={localCategories}
                    onCategorize={onCategorize}
                    onShowToast={handleShowToast}
                    onCategoryCreated={handleCategoryCreated}
                  />
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
              {onEdit && (
                <td style={{ textAlign: 'center' }}>
                  <ActionIconButton
                    onClick={() => onEdit(transaction)}
                    title="Edit transaction"
                    icon={<EditIcon fontSize="small" />}
                    color="primary"
                  />
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  )
}
