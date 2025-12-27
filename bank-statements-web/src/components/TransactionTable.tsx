import { format } from 'date-fns'
import { useState, useCallback, useEffect } from 'react'
import { Category, Transaction, Account } from '../types/Transaction'
import { Toast, ToastProps } from './Toast'
import { ConfirmationModal } from './ConfirmationModal'
import { CategorySelector } from './CategorySelector'
import { useApi } from '../api/ApiContext'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import { ActionIconButton } from './ActionIconButton'

export type TransactionSortField = 'date' | 'description' | 'amount' | 'created_at'
export type TransactionSortDirection = 'asc' | 'desc'

interface BulkCategorizeResult {
  updated_count: number
  message: string
}

export interface SimilarCountFilters {
  account_id?: string
  start_date?: string
  end_date?: string
  exclude_transfers?: boolean
}

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  accounts: Account[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => Promise<void>
  onBulkCategorize?: (normalizedDescription: string, categoryId: string) => Promise<BulkCategorizeResult | null>
  onBulkReplaceCategory?: (fromCategoryId: string, toCategoryId: string) => Promise<BulkCategorizeResult | null>
  similarCountFilters?: SimilarCountFilters
  onEdit?: (transaction: Transaction) => void
  onDelete?: (transaction: Transaction) => Promise<boolean>
  sortField?: TransactionSortField
  sortDirection?: TransactionSortDirection
  onSort?: (field: TransactionSortField) => void
  showRunningBalance?: boolean
}

interface CategoryCellProps {
  transaction: Transaction
  categories: Category[]
  onCategorize: (transactionId: string, categoryId?: string) => Promise<void>
  onBulkCategorize?: (normalizedDescription: string, categoryId: string) => Promise<BulkCategorizeResult | null>
  onBulkReplaceCategory?: (fromCategoryId: string, toCategoryId: string) => Promise<BulkCategorizeResult | null>
  similarCountFilters?: SimilarCountFilters
  onShowToast: (toast: Omit<ToastProps, 'onClose'>) => void
  onCategoryCreated: (category: Category) => void
}

const CategoryCell = ({
  transaction,
  categories,
  onCategorize,
  onBulkCategorize,
  onBulkReplaceCategory,
  similarCountFilters,
  onShowToast,
  onCategoryCreated,
}: CategoryCellProps) => {
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
        } else if (categoryId && onBulkCategorize) {
          const categoryName = categories.find((c) => c.id === categoryId)?.name || 'Category'
          const actions: { label: string; onClick: () => Promise<void> }[] = []

          const countResult = await apiClient.transactions.countSimilar({
            normalized_description: transaction.normalized_description,
            ...similarCountFilters,
          })
          const similarCount = countResult.count - 1

          if (similarCount > 0) {
            actions.push({
              label: `Apply to ${similarCount} similar`,
              onClick: async () => {
                const result = await onBulkCategorize(transaction.normalized_description, categoryId)
                if (result) {
                  const additionalCount = result.updated_count - 1
                  if (additionalCount > 0) {
                    onShowToast({
                      message: `Updated ${additionalCount} similar transaction${additionalCount === 1 ? '' : 's'}`,
                      type: 'success',
                    })
                  }
                }
              },
            })
          }

          if (previousCategoryId && onBulkReplaceCategory) {
            const oldCategoryName = categories.find((c) => c.id === previousCategoryId)?.name || 'old category'
            const replaceCountResult = await apiClient.transactions.countByCategory({
              category_id: previousCategoryId,
              ...similarCountFilters,
            })
            const replaceCount = replaceCountResult.count

            if (replaceCount > 0) {
              actions.push({
                label: `Replace ${replaceCount} from ${oldCategoryName}`,
                onClick: async () => {
                  const result = await onBulkReplaceCategory(previousCategoryId, categoryId)
                  if (result && result.updated_count > 0) {
                    onShowToast({
                      message: `Replaced category for ${result.updated_count} transaction${result.updated_count === 1 ? '' : 's'}`,
                      type: 'success',
                    })
                  }
                },
              })
            }
          }

          if (actions.length > 0) {
            onShowToast({
              message: `${categoryName} applied`,
              type: 'success',
              actions,
            })
          } else {
            onShowToast({
              message: `${categoryName} applied`,
              type: 'success',
            })
          }
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
    [
      transaction.id,
      transaction.category_id,
      transaction.normalized_description,
      categories,
      onCategorize,
      onBulkCategorize,
      onBulkReplaceCategory,
      similarCountFilters,
      apiClient,
      onShowToast,
    ]
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
  onBulkCategorize,
  onBulkReplaceCategory,
  similarCountFilters,
  onEdit,
  onDelete,
  sortField,
  sortDirection,
  onSort,
  showRunningBalance = false,
}: TransactionTableProps) => {
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [localCategories, setLocalCategories] = useState<Category[]>(categories)
  const [pendingDeleteTransaction, setPendingDeleteTransaction] = useState<Transaction | null>(null)

  useEffect(() => {
    setLocalCategories(categories)
  }, [categories])

  const handleShowToast = useCallback((toastProps: Omit<ToastProps, 'onClose'>) => {
    setToast(toastProps)
  }, [])

  const handleCategoryCreated = useCallback((newCategory: Category) => {
    setLocalCategories((prev) => [...prev, newCategory].sort((a, b) => a.name.localeCompare(b.name)))
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!pendingDeleteTransaction || !onDelete) return
    const success = await onDelete(pendingDeleteTransaction)
    if (success) {
      handleShowToast({ message: 'Transaction deleted', type: 'success' })
    } else {
      handleShowToast({ message: 'Failed to delete transaction', type: 'error' })
    }
    setPendingDeleteTransaction(null)
  }, [pendingDeleteTransaction, onDelete, handleShowToast])

  if (loading) {
    return <div className="loading">Loading transactions...</div>
  }

  if (transactions.length === 0) {
    return <div className="no-data">No transactions found. Add one to get started!</div>
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy-MM-dd')
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
          <col style={{ width: '10%' }} />
          <col style={{ width: onCategorize ? '33%' : '52%' }} />
          {onCategorize && <col style={{ width: '29%' }} />}
          <col style={{ width: '10%' }} />
          <col style={{ width: onCategorize ? '8%' : '18%' }} />
          {(onEdit || onDelete) && <col style={{ width: '10%' }} />}
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
              <th style={{ textAlign: 'left' }}>Account</th>
            )}
            {(onEdit || onDelete) && <th style={{ textAlign: 'center' }}>Actions</th>}
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
                    onBulkCategorize={onBulkCategorize}
                    onBulkReplaceCategory={onBulkReplaceCategory}
                    similarCountFilters={similarCountFilters}
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
              {(onEdit || onDelete) && (
                <td style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                    {onEdit && (
                      <ActionIconButton
                        onClick={() => onEdit(transaction)}
                        title="Edit transaction"
                        icon={<EditIcon fontSize="small" />}
                        color="primary"
                      />
                    )}
                    {onDelete && (
                      <ActionIconButton
                        onClick={() => setPendingDeleteTransaction(transaction)}
                        title="Delete transaction"
                        icon={<DeleteIcon fontSize="small" />}
                        color="error"
                      />
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      {pendingDeleteTransaction && (
        <ConfirmationModal
          isOpen={true}
          title="Delete Transaction"
          message={`${pendingDeleteTransaction.description} — ${formatDate(pendingDeleteTransaction.date)} — ${formatAmount(pendingDeleteTransaction.amount)}${pendingDeleteTransaction.category_id ? ` — ${localCategories.find((c) => c.id === pendingDeleteTransaction.category_id)?.name || ''}` : ''}`}
          confirmText="Delete"
          onConfirm={handleConfirmDelete}
          onCancel={() => setPendingDeleteTransaction(null)}
          dangerous
        />
      )}
    </div>
  )
}
