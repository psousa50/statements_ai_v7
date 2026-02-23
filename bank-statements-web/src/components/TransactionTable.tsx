import { format } from 'date-fns'
import { useState, useCallback, useEffect } from 'react'
import Chip from '@mui/material/Chip'
import Popover from '@mui/material/Popover'
import LocalOfferOutlinedIcon from '@mui/icons-material/LocalOfferOutlined'
import { Category, Transaction, Account, Tag } from '../types/Transaction'
import { Toast, ToastProps } from './Toast'
import { ConfirmationModal } from './ConfirmationModal'
import { BulkCategorizeModal } from './BulkCategorizeModal'
import { CategorySelector } from './CategorySelector'
import { TagInput } from './TagInput'
import { useApi } from '../api/ApiContext'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import Checkbox from '@mui/material/Checkbox'
import IconButton from '@mui/material/IconButton'
import { ActionIconButton } from './ActionIconButton'
import { formatCurrency } from '../utils/format'

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
  enhancement_rule_id?: string
}

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  accounts: Account[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => Promise<void>
  onBulkCategorize?: (
    normalizedDescription: string,
    categoryId: string,
    filters: SimilarCountFilters
  ) => Promise<BulkCategorizeResult | null>
  onBulkReplaceCategory?: (fromCategoryId: string, toCategoryId: string) => Promise<BulkCategorizeResult | null>
  similarCountFilters?: SimilarCountFilters
  onEdit?: (transaction: Transaction) => void
  onDelete?: (transaction: Transaction) => Promise<boolean>
  sortField?: TransactionSortField
  sortDirection?: TransactionSortDirection
  onSort?: (field: TransactionSortField) => void
  showRunningBalance?: boolean
  allTags?: Tag[]
  onAddTag?: (transactionId: string, tagId: string) => Promise<unknown>
  onRemoveTag?: (transactionId: string, tagId: string) => Promise<unknown>
  onCreateTag?: (name: string) => Promise<Tag | null>
  selectedIds?: Set<string>
  onToggleSelect?: (transactionId: string) => void
  onToggleSelectAll?: () => void
  onBulkTag?: (tagId: string) => Promise<unknown>
  onBulkCategorizeByIds?: (categoryId?: string) => Promise<unknown>
  onToggleExcludeFromAnalytics?: (transactionId: string, exclude: boolean) => Promise<unknown>
}

interface BulkModalState {
  normalizedDescription: string
  categoryId: string
  categoryName: string
  previousCategoryId?: string
  similarCount: number
  replaceOption?: { categoryName: string; count: number }
}

interface CategoryCellProps {
  transaction: Transaction
  categories: Category[]
  onCategorize: (transactionId: string, categoryId?: string) => Promise<void>
  onBulkCategorize?: (
    normalizedDescription: string,
    categoryId: string,
    filters: SimilarCountFilters
  ) => Promise<BulkCategorizeResult | null>
  onBulkReplaceCategory?: (fromCategoryId: string, toCategoryId: string) => Promise<BulkCategorizeResult | null>
  similarCountFilters?: SimilarCountFilters
  onShowToast: (toast: Omit<ToastProps, 'onClose'>) => void
  onCategoryCreated: (category: Category) => void
  onShowBulkModal: (state: BulkModalState) => void
}

const getCategoryDisplayName = (category: Category | undefined): string => {
  if (!category) return 'Unknown'
  if (category.parent) {
    return `${category.parent.name} > ${category.name}`
  }
  return category.name
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
  onShowBulkModal,
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
          const removedCategory = categories.find((c) => c.id === previousCategoryId)
          const removedCategoryName = getCategoryDisplayName(removedCategory)
          onShowToast({
            message: `${removedCategoryName} removed`,
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
          const category = categories.find((c) => c.id === categoryId)
          const categoryName = getCategoryDisplayName(category)

          const countResult = await apiClient.transactions.countSimilar({
            normalized_description: transaction.normalized_description,
            ...similarCountFilters,
          })
          const similarCount = countResult.count - 1

          let replaceOption: { categoryName: string; count: number } | undefined
          if (previousCategoryId && onBulkReplaceCategory) {
            const oldCategory = categories.find((c) => c.id === previousCategoryId)
            const oldCategoryName = getCategoryDisplayName(oldCategory)
            const replaceCountResult = await apiClient.transactions.countByCategory({
              category_id: previousCategoryId,
              ...similarCountFilters,
            })
            if (replaceCountResult.count > 0) {
              replaceOption = { categoryName: oldCategoryName, count: replaceCountResult.count }
            }
          }

          if (similarCount > 0 || replaceOption) {
            onShowBulkModal({
              normalizedDescription: transaction.normalized_description,
              categoryId,
              categoryName,
              previousCategoryId,
              similarCount,
              replaceOption,
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
      onShowBulkModal,
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
  allTags,
  onAddTag,
  onRemoveTag,
  onCreateTag,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onBulkTag,
  onBulkCategorizeByIds,
  onToggleExcludeFromAnalytics,
}: TransactionTableProps) => {
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [localCategories, setLocalCategories] = useState<Category[]>(categories)
  const [pendingDeleteTransaction, setPendingDeleteTransaction] = useState<Transaction | null>(null)
  const [bulkModal, setBulkModal] = useState<BulkModalState | null>(null)
  const [tagPopover, setTagPopover] = useState<{ anchorEl: HTMLElement; transactionId: string } | null>(null)
  const tagPopoverOpen = Boolean(tagPopover)
  const tagPopoverTransaction = tagPopover ? transactions.find((t) => t.id === tagPopover.transactionId) : null

  useEffect(() => {
    setLocalCategories(categories)
  }, [categories])

  const handleShowToast = useCallback((toastProps: Omit<ToastProps, 'onClose'>) => {
    setToast(toastProps)
  }, [])

  const handleShowBulkModal = useCallback((state: BulkModalState) => {
    setBulkModal(state)
  }, [])

  const handleApplyToSimilar = useCallback(async () => {
    if (!bulkModal || !onBulkCategorize) return
    const result = await onBulkCategorize(
      bulkModal.normalizedDescription,
      bulkModal.categoryId,
      similarCountFilters || {}
    )
    if (result) {
      const additionalCount = result.updated_count - 1
      if (additionalCount > 0) {
        handleShowToast({
          message: `Updated ${additionalCount} similar transaction${additionalCount === 1 ? '' : 's'}`,
          type: 'success',
        })
      }
    }
    setBulkModal(null)
  }, [bulkModal, onBulkCategorize, similarCountFilters, handleShowToast])

  const handleReplaceFromCategory = useCallback(async () => {
    if (!bulkModal?.previousCategoryId || !onBulkReplaceCategory) return
    const result = await onBulkReplaceCategory(bulkModal.previousCategoryId, bulkModal.categoryId)
    if (result && result.updated_count > 0) {
      handleShowToast({
        message: `Replaced category for ${result.updated_count} transaction${result.updated_count === 1 ? '' : 's'}`,
        type: 'success',
      })
    }
    setBulkModal(null)
  }, [bulkModal, onBulkReplaceCategory, handleShowToast])

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

  const selectionAwareAddTag = useCallback(
    async (transactionId: string, tagId: string) => {
      const result = await onAddTag?.(transactionId, tagId)
      if (result && selectedIds && selectedIds.size > 0 && onBulkTag) {
        const tagName = allTags?.find((t) => t.id === tagId)?.name || 'tag'
        handleShowToast({
          message: `Apply "${tagName}" to ${selectedIds.size} selected?`,
          type: 'info',
          duration: 6000,
          action: { label: 'Apply', onClick: () => onBulkTag(tagId) },
        })
      }
      return result
    },
    [onAddTag, selectedIds, onBulkTag, allTags, handleShowToast]
  )

  const selectionAwareCategorize = useCallback(
    async (transactionId: string, categoryId?: string) => {
      await onCategorize?.(transactionId, categoryId)
      if (categoryId && selectedIds && selectedIds.size > 0 && onBulkCategorizeByIds) {
        const category = localCategories.find((c) => c.id === categoryId)
        const categoryName = category ? getCategoryDisplayName(category) : 'category'
        handleShowToast({
          message: `Apply "${categoryName}" to ${selectedIds.size} selected?`,
          type: 'info',
          duration: 6000,
          action: { label: 'Apply', onClick: () => onBulkCategorizeByIds(categoryId) },
        })
      }
    },
    [onCategorize, selectedIds, onBulkCategorizeByIds, localCategories, handleShowToast]
  )

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

  const getAccountCurrency = (accountId?: string) => {
    if (!accountId) return 'EUR'
    const account = accounts.find((a) => a.id === accountId)
    return account?.currency ?? 'EUR'
  }

  const formatAmount = (amount: number, accountId?: string) => {
    return formatCurrency(amount, getAccountCurrency(accountId))
  }

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
          {onToggleSelect && <col style={{ width: '40px' }} />}
          <col style={{ width: '10%' }} />
          <col style={{ width: onCategorize ? '33%' : '52%' }} />
          {onCategorize && <col style={{ width: '29%' }} />}
          <col style={{ width: '10%' }} />
          <col style={{ width: onCategorize ? '8%' : '18%' }} />
          {(onEdit || onDelete) && <col style={{ width: '10%' }} />}
        </colgroup>
        <thead>
          <tr>
            {onToggleSelect &&
              (() => {
                const pageIds = transactions.map((t) => t.id)
                const selectedOnPage = pageIds.filter((id) => selectedIds?.has(id)).length
                const allSelected = selectedOnPage === pageIds.length && pageIds.length > 0
                const indeterminate = selectedOnPage > 0 && !allSelected
                return (
                  <th style={{ textAlign: 'center', width: 40 }}>
                    <Checkbox
                      size="small"
                      checked={allSelected}
                      indeterminate={indeterminate}
                      onChange={onToggleSelectAll}
                      sx={{ padding: '2px' }}
                    />
                  </th>
                )
              })()}
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
            <tr
              key={transaction.id}
              className={`${selectedIds?.has(transaction.id) ? 'selected' : ''} ${transaction.exclude_from_analytics ? 'excluded' : ''}`}
              {...(transaction.exclude_from_analytics ? { 'data-excluded': 'true' } : {})}
            >
              {onToggleSelect && (
                <td style={{ textAlign: 'center', width: 40 }}>
                  <Checkbox
                    size="small"
                    checked={selectedIds?.has(transaction.id) ?? false}
                    onChange={() => onToggleSelect(transaction.id)}
                    sx={{ padding: '2px' }}
                  />
                </td>
              )}
              <td>{formatDate(transaction.date)}</td>
              <td>
                <div className="transaction-description">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {transaction.exclude_from_analytics && (
                      <VisibilityOffIcon data-testid="excluded-indicator" sx={{ fontSize: 14, opacity: 0.5 }} />
                    )}
                    {transaction.description}
                  </div>
                  {transaction.counterparty_account_id && (
                    <div className={`counterparty-badge ${transaction.amount < 0 ? 'negative' : 'positive'}`}>
                      {transaction.amount < 0 ? 'to' : 'from'}: {getAccountName(transaction.counterparty_account_id)}
                    </div>
                  )}
                  {transaction.tags && transaction.tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginTop: 2 }}>
                      {transaction.tags.map((tag) => (
                        <Chip
                          key={tag.id}
                          label={tag.name}
                          variant="outlined"
                          size="small"
                          onClick={onRemoveTag ? () => onRemoveTag(transaction.id, tag.id) : undefined}
                          sx={{
                            height: 18,
                            fontSize: '0.65rem',
                            opacity: 0.75,
                            cursor: onRemoveTag ? 'pointer' : undefined,
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </td>
              {onCategorize && (
                <td>
                  <CategoryCell
                    transaction={transaction}
                    categories={localCategories}
                    onCategorize={selectionAwareCategorize}
                    onBulkCategorize={onBulkCategorize}
                    onBulkReplaceCategory={onBulkReplaceCategory}
                    similarCountFilters={similarCountFilters}
                    onShowToast={handleShowToast}
                    onCategoryCreated={handleCategoryCreated}
                    onShowBulkModal={handleShowBulkModal}
                  />
                </td>
              )}
              <td className={`text-right ${transaction.amount < 0 ? 'negative' : 'positive'}`}>
                {formatAmount(transaction.amount, transaction.account_id)}
              </td>
              {showRunningBalance ? (
                <td className="running-balance text-right">
                  {transaction.running_balance !== undefined
                    ? formatAmount(transaction.running_balance, transaction.account_id)
                    : '-'}
                </td>
              ) : (
                <td>{getAccountName(transaction.account_id)}</td>
              )}
              {(onEdit || onDelete) && (
                <td style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                    {onToggleExcludeFromAnalytics && (
                      <IconButton
                        size="small"
                        aria-label={
                          transaction.exclude_from_analytics ? 'include in analytics' : 'exclude from analytics'
                        }
                        onClick={() =>
                          onToggleExcludeFromAnalytics(transaction.id, !transaction.exclude_from_analytics)
                        }
                        sx={{
                          minWidth: 0,
                          padding: '4px',
                          width: 28,
                          height: 28,
                          transition: 'all 0.2s',
                          '&:hover': { transform: 'scale(1.1)' },
                        }}
                      >
                        <VisibilityOffIcon
                          fontSize="small"
                          sx={{ opacity: transaction.exclude_from_analytics ? 1 : 0.4 }}
                        />
                      </IconButton>
                    )}
                    {allTags && onAddTag && onRemoveTag && onCreateTag && (
                      <IconButton
                        size="small"
                        title="Manage tags"
                        onClick={(e) => setTagPopover({ anchorEl: e.currentTarget, transactionId: transaction.id })}
                        sx={{
                          minWidth: 0,
                          padding: '4px',
                          width: 28,
                          height: 28,
                          transition: 'all 0.2s',
                          '&:hover': { transform: 'scale(1.1)' },
                        }}
                      >
                        <LocalOfferOutlinedIcon fontSize="small" />
                      </IconButton>
                    )}
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
          message={`${pendingDeleteTransaction.description} — ${formatDate(pendingDeleteTransaction.date)} — ${formatAmount(pendingDeleteTransaction.amount, pendingDeleteTransaction.account_id)}${pendingDeleteTransaction.category_id ? ` — ${localCategories.find((c) => c.id === pendingDeleteTransaction.category_id)?.name || ''}` : ''}`}
          confirmText="Delete"
          onConfirm={handleConfirmDelete}
          onCancel={() => setPendingDeleteTransaction(null)}
          dangerous
        />
      )}
      {bulkModal && (
        <BulkCategorizeModal
          isOpen={true}
          categoryName={bulkModal.categoryName}
          normalizedDescription={bulkModal.normalizedDescription}
          similarCount={bulkModal.similarCount}
          replaceOption={bulkModal.replaceOption}
          onApplyToSimilar={handleApplyToSimilar}
          onReplaceFromCategory={bulkModal.replaceOption ? handleReplaceFromCategory : undefined}
          onDismiss={() => setBulkModal(null)}
        />
      )}
      {allTags && onAddTag && onRemoveTag && onCreateTag && (
        <Popover
          open={tagPopoverOpen}
          anchorEl={tagPopover?.anchorEl}
          onClose={() => setTagPopover(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
          transformOrigin={{ vertical: 'top', horizontal: 'left' }}
          slotProps={{ paper: { sx: { p: 1.5, minWidth: 220 } } }}
        >
          {tagPopoverTransaction && (
            <TagInput
              transactionId={tagPopoverTransaction.id}
              currentTags={tagPopoverTransaction.tags || []}
              allTags={allTags}
              onAddTag={selectionAwareAddTag}
              onRemoveTag={onRemoveTag}
              onCreateTag={onCreateTag}
              autoFocus
            />
          )}
        </Popover>
      )}
    </div>
  )
}
