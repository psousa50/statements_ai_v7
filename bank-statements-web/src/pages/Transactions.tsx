import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTransactions } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { useAccounts } from '../services/hooks/useAccounts'
import {
  TransactionTable,
  TransactionSortField,
  TransactionSortDirection,
  SimilarCountFilters,
} from '../components/TransactionTable'
import { TransactionFilters, CategorizationFilter } from '../components/TransactionFilters'
import { TransactionModal } from '../components/TransactionModal'
import { Pagination } from '../components/Pagination'
import { CategorizationStatus, TransactionCreate, Transaction } from '../types/Transaction'
import { TransactionFilters as FilterType, transactionClient } from '../api/TransactionClient'
import { formatCurrency } from '../utils/format'
import './TransactionsPage.css'

function convertAmountFiltersForApi(
  minAmount: number | undefined,
  maxAmount: number | undefined,
  transactionType: 'all' | 'debit' | 'credit'
): { min_amount?: number; max_amount?: number } {
  if (minAmount === undefined && maxAmount === undefined) {
    return {}
  }

  const bothPositive = (minAmount === undefined || minAmount >= 0) && (maxAmount === undefined || maxAmount >= 0)

  if (transactionType === 'debit' && bothPositive) {
    return {
      min_amount: maxAmount !== undefined ? -maxAmount : undefined,
      max_amount: minAmount !== undefined ? -minAmount : undefined,
    }
  }

  return { min_amount: minAmount, max_amount: maxAmount }
}

export const TransactionsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const getInitialFilters = (): FilterType => {
    const urlDescriptionSearch = searchParams.get('description_search')
    const urlMinAmount = searchParams.get('min_amount')
    const urlMaxAmount = searchParams.get('max_amount')
    const urlStartDate = searchParams.get('start_date')
    const urlEndDate = searchParams.get('end_date')
    const urlStatus = searchParams.get('status')
    const urlAccountId = searchParams.get('account_id')
    const urlCategoryIds = searchParams.get('category_ids')
    const urlSortField = searchParams.get('sort_field')
    const urlSortDirection = searchParams.get('sort_direction')
    const urlEnhancementRuleId = searchParams.get('enhancement_rule_id')
    const urlExcludeTransfers = searchParams.get('exclude_transfers')
    const urlExcludeUncategorized = searchParams.get('exclude_uncategorized')
    const urlTransactionType = searchParams.get('transaction_type')
    const urlTransactionIds = searchParams.get('transaction_ids')
    const urlSavedFilterId = searchParams.get('saved_filter_id')

    return {
      page: 1,
      page_size: 20,
      description_search: urlDescriptionSearch || undefined,
      min_amount: urlMinAmount ? parseFloat(urlMinAmount) : undefined,
      max_amount: urlMaxAmount ? parseFloat(urlMaxAmount) : undefined,
      start_date: urlStartDate || undefined,
      end_date: urlEndDate || undefined,
      status: (urlStatus as CategorizationStatus) || undefined,
      account_id: urlAccountId || undefined,
      category_ids: urlCategoryIds ? urlCategoryIds.split(',') : undefined,
      sort_field: (urlSortField as TransactionSortField) || 'date',
      sort_direction: (urlSortDirection as TransactionSortDirection) || 'desc',
      enhancement_rule_id: urlEnhancementRuleId || undefined,
      exclude_transfers: urlExcludeTransfers === 'false' ? false : true,
      exclude_uncategorized: urlExcludeUncategorized === 'true' ? true : false,
      transaction_type: (urlTransactionType as 'all' | 'debit' | 'credit') || 'all',
      transaction_ids: urlTransactionIds ? urlTransactionIds.split(',') : undefined,
      saved_filter_id: urlSavedFilterId || undefined,
    }
  }

  const [filters, setFilters] = useState<FilterType>(getInitialFilters())

  const patternLabel = searchParams.get('pattern_label')
  const hasPatternFilter = !!(filters.transaction_ids?.length || filters.saved_filter_id)

  // Local state for debounced inputs - initialize from URL params
  const [localDescriptionSearch, setLocalDescriptionSearch] = useState<string>(
    searchParams.get('description_search') || ''
  )
  const [localMinAmount, setLocalMinAmount] = useState<number | undefined>(
    searchParams.get('min_amount') ? parseFloat(searchParams.get('min_amount')!) : undefined
  )
  const [localMaxAmount, setLocalMaxAmount] = useState<number | undefined>(
    searchParams.get('max_amount') ? parseFloat(searchParams.get('max_amount')!) : undefined
  )
  const [localStartDate, setLocalStartDate] = useState<string>(searchParams.get('start_date') || '')
  const [localEndDate, setLocalEndDate] = useState<string>(searchParams.get('end_date') || '')
  const [categorizationFilter, setCategorizationFilter] = useState<CategorizationFilter>(() => {
    const urlStatus = searchParams.get('status')
    if (urlStatus === 'UNCATEGORIZED') return 'uncategorized'
    const urlExcludeUncategorized = searchParams.get('exclude_uncategorized')
    if (urlExcludeUncategorized === 'true') return 'categorized'
    return 'all'
  })

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()
  const bottomPaginationRef = useRef<HTMLDivElement>(null)
  const [isBottomPaginationVisible, setIsBottomPaginationVisible] = useState(true)

  const {
    transactions,
    loading: transactionsLoading,
    error: transactionsError,
    enhancementRule,
    pagination,
    fetchTransactions,
    addTransaction,
    updateTransaction,
    categorizeTransaction,
    bulkUpdateCategory,
    bulkReplaceCategory,
    deleteTransaction,
  } = useTransactions()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()
  const { accounts, loading: accountsLoading, error: accountsError } = useAccounts()

  const loading = transactionsLoading || categoriesLoading || accountsLoading
  const error = transactionsError || categoriesError || accountsError

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<Transaction | undefined>(undefined)
  const [isExporting, setIsExporting] = useState(false)

  const isRuleFiltering = !!filters.enhancement_rule_id

  // Update filters when URL changes
  useEffect(() => {
    const newFilters = getInitialFilters()
    setFilters(newFilters)

    // Update local state for debounced inputs
    setLocalDescriptionSearch(searchParams.get('description_search') || '')
    setLocalMinAmount(searchParams.get('min_amount') ? parseFloat(searchParams.get('min_amount')!) : undefined)
    setLocalMaxAmount(searchParams.get('max_amount') ? parseFloat(searchParams.get('max_amount')!) : undefined)
    setLocalStartDate(searchParams.get('start_date') || '')
    setLocalEndDate(searchParams.get('end_date') || '')
  }, [searchParams])

  // Load data on mount with initial filters from URL
  useEffect(() => {
    const convertedAmounts = convertAmountFiltersForApi(
      filters.min_amount,
      filters.max_amount,
      filters.transaction_type || 'all'
    )
    fetchTransactions({
      ...filters,
      ...convertedAmounts,
      include_running_balance: !!filters.account_id,
    })
  }, [fetchTransactions, filters])

  // Debounced filter update for search, amount, and date inputs
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = setTimeout(() => {
      const needsUpdate =
        localDescriptionSearch !== (filters.description_search || '') ||
        localMinAmount !== filters.min_amount ||
        localMaxAmount !== filters.max_amount ||
        localStartDate !== (filters.start_date || '') ||
        localEndDate !== (filters.end_date || '')

      if (needsUpdate) {
        const convertedAmounts = convertAmountFiltersForApi(
          localMinAmount,
          localMaxAmount,
          filters.transaction_type || 'all'
        )
        const updatedFilters = {
          ...filters,
          description_search: localDescriptionSearch || undefined,
          min_amount: localMinAmount,
          max_amount: localMaxAmount,
          start_date: localStartDate || undefined,
          end_date: localEndDate || undefined,
          page: 1,
          include_running_balance: !!filters.account_id,
        }
        setFilters(updatedFilters)
        fetchTransactions({
          ...updatedFilters,
          ...convertedAmounts,
        })
      }
    }, 500) // 500ms debounce

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [localDescriptionSearch, localMinAmount, localMaxAmount, localStartDate, localEndDate, filters, fetchTransactions])

  useEffect(() => {
    const params = new URLSearchParams()

    if (filters.description_search) params.set('description_search', filters.description_search)
    if (filters.category_ids?.length) params.set('category_ids', filters.category_ids.join(','))
    if (filters.account_id) params.set('account_id', filters.account_id)
    if (filters.min_amount !== undefined) params.set('min_amount', filters.min_amount.toString())
    if (filters.max_amount !== undefined) params.set('max_amount', filters.max_amount.toString())
    if (filters.start_date) params.set('start_date', filters.start_date)
    if (filters.end_date) params.set('end_date', filters.end_date)
    if (filters.status) params.set('status', filters.status)
    if (filters.sort_field && filters.sort_field !== 'date') params.set('sort_field', filters.sort_field)
    if (filters.sort_direction && filters.sort_direction !== 'desc')
      params.set('sort_direction', filters.sort_direction)
    if (filters.enhancement_rule_id) params.set('enhancement_rule_id', filters.enhancement_rule_id)
    if (filters.exclude_transfers === false) params.set('exclude_transfers', 'false')
    if (filters.exclude_uncategorized) params.set('exclude_uncategorized', 'true')
    if (filters.transaction_type && filters.transaction_type !== 'all')
      params.set('transaction_type', filters.transaction_type)
    if (filters.transaction_ids?.length) params.set('transaction_ids', filters.transaction_ids.join(','))
    if (filters.saved_filter_id) params.set('saved_filter_id', filters.saved_filter_id)

    const patternLabelParam = searchParams.get('pattern_label')
    if (patternLabelParam) params.set('pattern_label', patternLabelParam)

    setSearchParams(params, { replace: true })
  }, [filters, setSearchParams, searchParams])

  useEffect(() => {
    const element = bottomPaginationRef.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsBottomPaginationVisible(entry.isIntersecting)
      },
      { threshold: 0.1 }
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [pagination?.total_count, loading])

  const handleFilterChange = useCallback(
    (newFilters: Partial<FilterType>) => {
      const updatedFilters = {
        ...filters,
        ...newFilters,
        page: 1,
        include_running_balance: !!newFilters.account_id,
      }
      setFilters(updatedFilters)
      const convertedAmounts = convertAmountFiltersForApi(
        updatedFilters.min_amount,
        updatedFilters.max_amount,
        updatedFilters.transaction_type || 'all'
      )
      fetchTransactions({
        ...updatedFilters,
        ...convertedAmounts,
      })
    },
    [filters, fetchTransactions]
  )

  const handlePageChange = useCallback(
    (page: number) => {
      const updatedFilters = {
        ...filters,
        page,
        include_running_balance: !!filters.account_id,
      }
      setFilters(updatedFilters)
      const convertedAmounts = convertAmountFiltersForApi(
        filters.min_amount,
        filters.max_amount,
        filters.transaction_type || 'all'
      )
      fetchTransactions({
        ...updatedFilters,
        ...convertedAmounts,
      })
    },
    [filters, fetchTransactions]
  )

  const handlePageSizeChange = useCallback(
    (page_size: number) => {
      const updatedFilters = {
        ...filters,
        page_size,
        page: 1,
        include_running_balance: !!filters.account_id,
      }
      setFilters(updatedFilters)
      const convertedAmounts = convertAmountFiltersForApi(
        filters.min_amount,
        filters.max_amount,
        filters.transaction_type || 'all'
      )
      fetchTransactions({
        ...updatedFilters,
        ...convertedAmounts,
      })
    },
    [filters, fetchTransactions]
  )

  // Immediate updates (no debouncing needed)
  const handleCategoryFilter = useCallback(
    (categoryIds: string[]) => {
      handleFilterChange({ category_ids: categoryIds })
    },
    [handleFilterChange]
  )

  const handleAccountFilter = useCallback(
    (accountId?: string) => {
      handleFilterChange({ account_id: accountId })
    },
    [handleFilterChange]
  )

  const handleExcludeTransfersFilter = useCallback(
    (excludeTransfers: boolean) => {
      handleFilterChange({ exclude_transfers: excludeTransfers })
    },
    [handleFilterChange]
  )

  const handleCategorizationFilterChange = useCallback(
    (filter: CategorizationFilter) => {
      setCategorizationFilter(filter)
      if (filter === 'uncategorized') {
        handleFilterChange({ status: 'UNCATEGORIZED', exclude_uncategorized: undefined })
      } else if (filter === 'categorized') {
        handleFilterChange({ exclude_uncategorized: true, status: undefined })
      } else {
        handleFilterChange({ exclude_uncategorized: undefined, status: undefined })
      }
    },
    [handleFilterChange]
  )

  const handleTransactionTypeFilter = useCallback(
    (transactionType: 'all' | 'debit' | 'credit') => {
      handleFilterChange({ transaction_type: transactionType })
    },
    [handleFilterChange]
  )

  const handleSort = useCallback(
    (field: TransactionSortField) => {
      const currentSortField = filters.sort_field
      const currentSortDirection = filters.sort_direction || 'desc'

      let newSortDirection: TransactionSortDirection
      if (currentSortField === field) {
        // Toggle direction if same field
        newSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc'
      } else {
        // Default to desc for new field
        newSortDirection = 'desc'
      }

      handleFilterChange({
        sort_field: field,
        sort_direction: newSortDirection,
      })
    },
    [filters.sort_field, filters.sort_direction, handleFilterChange]
  )

  // Debounced updates (local state only)
  const handleAmountRangeFilter = useCallback((minAmount?: number, maxAmount?: number) => {
    setLocalMinAmount(minAmount)
    setLocalMaxAmount(maxAmount)
  }, [])

  const handleDescriptionSearchFilter = useCallback((search?: string) => {
    setLocalDescriptionSearch(search || '')
  }, [])

  const handleDateRangeFilter = useCallback((startDate?: string, endDate?: string) => {
    setLocalStartDate(startDate ?? '')
    setLocalEndDate(endDate ?? '')
  }, [])

  const handleClearFilters = useCallback(() => {
    const clearedFilters = {
      page: 1,
      page_size: filters.page_size,
      sort_field: 'date' as TransactionSortField,
      sort_direction: 'desc' as TransactionSortDirection,
      include_running_balance: false,
    }
    setFilters(clearedFilters)
    setLocalDescriptionSearch('')
    setLocalMinAmount(undefined)
    setLocalMaxAmount(undefined)
    setLocalStartDate('')
    setLocalEndDate('')
    setCategorizationFilter('all')
    fetchTransactions(clearedFilters)
  }, [filters.page_size, fetchTransactions])

  const handleClearRuleFilter = useCallback(() => {
    const clearedFilters = {
      page: 1,
      page_size: filters.page_size,
      sort_field: 'date' as TransactionSortField,
      sort_direction: 'desc' as TransactionSortDirection,
      include_running_balance: false,
    }
    setFilters(clearedFilters)
    navigate('/transactions')
    fetchTransactions(clearedFilters)
  }, [filters.page_size, fetchTransactions, navigate])

  const handleClearPatternFilter = useCallback(() => {
    const { transaction_ids: _, saved_filter_id: __, ...remainingFilters } = filters
    const clearedFilters = {
      ...remainingFilters,
      page: 1,
      transaction_ids: undefined,
      saved_filter_id: undefined,
    }
    setFilters(clearedFilters)
    const params = new URLSearchParams(window.location.search)
    params.delete('transaction_ids')
    params.delete('saved_filter_id')
    params.delete('pattern_label')
    const newUrl = params.toString() ? `/transactions?${params.toString()}` : '/transactions'
    navigate(newUrl)
    const convertedAmounts = convertAmountFiltersForApi(
      clearedFilters.min_amount,
      clearedFilters.max_amount,
      clearedFilters.transaction_type || 'all'
    )
    fetchTransactions({ ...clearedFilters, ...convertedAmounts })
  }, [filters, fetchTransactions, navigate])

  const fetchWithConvertedAmounts = useCallback(() => {
    const convertedAmounts = convertAmountFiltersForApi(
      filters.min_amount,
      filters.max_amount,
      filters.transaction_type || 'all'
    )
    fetchTransactions({
      ...filters,
      ...convertedAmounts,
      include_running_balance: !!filters.account_id,
    })
  }, [filters, fetchTransactions])

  const handleCategorizeTransaction = async (transactionId: string, categoryId?: string) => {
    await categorizeTransaction(transactionId, categoryId)
    fetchWithConvertedAmounts()
  }

  const handleBulkCategorize = async (
    normalizedDescription: string,
    categoryId: string,
    similarFilters: SimilarCountFilters
  ) => {
    const result = await bulkUpdateCategory(normalizedDescription, categoryId, similarFilters)
    if (result) {
      fetchWithConvertedAmounts()
    }
    return result
  }

  const handleBulkReplaceCategory = async (fromCategoryId: string, toCategoryId: string) => {
    const result = await bulkReplaceCategory(fromCategoryId, toCategoryId, {
      account_id: filters.account_id,
      start_date: filters.start_date,
      end_date: filters.end_date,
      exclude_transfers: filters.exclude_transfers,
    })
    if (result) {
      fetchWithConvertedAmounts()
    }
    return result
  }

  const handleSaveTransaction = async (transactionData: TransactionCreate, transactionId?: string) => {
    if (transactionId) {
      const updatedTransaction = await updateTransaction(transactionId, transactionData)
      if (updatedTransaction) {
        fetchWithConvertedAmounts()
      }
      return updatedTransaction
    } else {
      const createdTransaction = await addTransaction(transactionData)
      if (createdTransaction) {
        fetchWithConvertedAmounts()
      }
      return createdTransaction
    }
  }

  const handleEditTransaction = (transaction: Transaction) => {
    setEditingTransaction(transaction)
    setIsModalOpen(true)
  }

  const handleDeleteTransaction = async (transaction: Transaction) => {
    return deleteTransaction(transaction.id)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingTransaction(undefined)
  }

  const handleExportCSV = async () => {
    setIsExporting(true)
    try {
      await transactionClient.exportCSV(filters)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="transactions-page">
      <header className="page-header">
        <div className="page-header-content">
          <div>
            <h1>Transactions</h1>
            <p className="page-description">
              View and manage your bank transactions with advanced filtering and categorization
            </p>
          </div>
          <div className="page-header-actions">
            <button
              className="button-secondary"
              onClick={handleExportCSV}
              disabled={isExporting || loading || transactions.length === 0}
            >
              {isExporting ? 'Exporting...' : 'Download CSV'}
            </button>
            <button className="button-primary" onClick={() => setIsModalOpen(true)}>
              + New Transaction
            </button>
          </div>
        </div>
      </header>

      {/* Enhancement Rule Filter Banner */}
      {isRuleFiltering && (
        <div className="rule-filter-banner">
          <div className="rule-filter-content">
            <span className="rule-filter-text">
              🔍 Filtered by rule: <strong>"{enhancementRule?.normalized_description_pattern || 'Loading...'}"</strong>
              {enhancementRule?.category && <span> → {enhancementRule.category.name}</span>}
            </span>
            <button
              className="rule-filter-clear-btn"
              onClick={handleClearRuleFilter}
              title="Return to normal transaction view"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Pattern Filter Banner */}
      {hasPatternFilter && (
        <div className="rule-filter-banner">
          <div className="rule-filter-content">
            <span className="rule-filter-text">
              🔍 {patternLabel || 'Recurring pattern'}
              {(filters.transaction_ids?.length || pagination?.total_count) &&
                ` (${filters.transaction_ids?.length || pagination?.total_count} transactions)`}
            </span>
            <button className="rule-filter-clear-btn" onClick={handleClearPatternFilter} title="Clear pattern filter">
              ✕
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="transactions-layout">
        {!isRuleFiltering && (
          <div className="filters-sidebar">
            <TransactionFilters
              categories={categories || []}
              accounts={accounts || []}
              selectedCategoryIds={filters.category_ids}
              selectedAccountId={filters.account_id}
              minAmount={localMinAmount}
              maxAmount={localMaxAmount}
              descriptionSearch={localDescriptionSearch}
              startDate={localStartDate}
              endDate={localEndDate}
              excludeTransfers={filters.exclude_transfers}
              categorizationFilter={categorizationFilter}
              transactionType={filters.transaction_type || 'all'}
              onCategoryChange={handleCategoryFilter}
              onAccountChange={handleAccountFilter}
              onAmountRangeChange={handleAmountRangeFilter}
              onDescriptionSearchChange={handleDescriptionSearchFilter}
              onDateRangeChange={handleDateRangeFilter}
              onExcludeTransfersChange={handleExcludeTransfersFilter}
              onCategorizationFilterChange={handleCategorizationFilterChange}
              onTransactionTypeChange={handleTransactionTypeFilter}
              onClearFilters={handleClearFilters}
            />
          </div>
        )}

        <div className="transactions-content">
          <div className="transactions-header">
            <div className="transactions-summary">
              <h2>Transactions</h2>
              {!loading &&
                transactions.length > 0 &&
                (() => {
                  const total = pagination.total_amount
                  return (
                    <div className="transactions-stats">
                      <span className="transaction-count">{pagination.total_count} transactions found</span>
                      <span className="transaction-total">
                        Total: <span className={total < 0 ? 'negative' : 'positive'}>{formatCurrency(total)}</span>
                      </span>
                    </div>
                  )
                })()}
            </div>
          </div>

          {!loading && pagination.total_count > 0 && !isBottomPaginationVisible && (
            <div className="transactions-pagination">
              <Pagination
                currentPage={pagination.current_page}
                totalPages={pagination.total_pages}
                totalItems={pagination.total_count}
                pageSize={pagination.page_size}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                itemName="transactions"
              />
            </div>
          )}

          <div className="transactions-table-container">
            <TransactionTable
              transactions={transactions || []}
              categories={categories || []}
              accounts={accounts || []}
              loading={loading}
              onCategorize={handleCategorizeTransaction}
              onBulkCategorize={handleBulkCategorize}
              onBulkReplaceCategory={handleBulkReplaceCategory}
              similarCountFilters={{
                account_id: filters.account_id,
                start_date: filters.start_date,
                end_date: filters.end_date,
                exclude_transfers: filters.exclude_transfers,
                enhancement_rule_id: filters.enhancement_rule_id,
              }}
              onEdit={handleEditTransaction}
              onDelete={handleDeleteTransaction}
              sortField={filters.sort_field as TransactionSortField}
              sortDirection={filters.sort_direction}
              onSort={handleSort}
              showRunningBalance={!!filters.account_id}
            />
          </div>

          <div ref={bottomPaginationRef}>
            {!loading && pagination.total_count > 0 && (
              <div className="transactions-pagination">
                <Pagination
                  currentPage={pagination.current_page}
                  totalPages={pagination.total_pages}
                  totalItems={pagination.total_count}
                  pageSize={pagination.page_size}
                  onPageChange={handlePageChange}
                  onPageSizeChange={handlePageSizeChange}
                  itemName="transactions"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <TransactionModal
        isOpen={isModalOpen}
        categories={categories || []}
        accounts={accounts || []}
        onSave={handleSaveTransaction}
        onClose={handleCloseModal}
        transaction={editingTransaction}
      />
    </div>
  )
}
