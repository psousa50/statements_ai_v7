import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTransactions } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { useAccounts } from '../services/hooks/useAccounts'
import { TransactionTable, TransactionSortField, TransactionSortDirection } from '../components/TransactionTable'
import { TransactionFilters } from '../components/TransactionFilters'
import { Pagination } from '../components/Pagination'
import { CategorizationStatus } from '../types/Transaction'
import { TransactionFilters as FilterType } from '../api/TransactionClient'
import './TransactionsPage.css'

export const TransactionsPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  // Initialize filters from URL parameters
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
    }
  }

  const [filters, setFilters] = useState<FilterType>(getInitialFilters())

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

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    transactions,
    loading: transactionsLoading,
    error: transactionsError,
    enhancementRule,
    pagination,
    fetchTransactions,
    categorizeTransaction,
  } = useTransactions()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()
  const { accounts, loading: accountsLoading, error: accountsError } = useAccounts()

  const loading = transactionsLoading || categoriesLoading || accountsLoading
  const error = transactionsError || categoriesError || accountsError

  // Track if we're in rule filtering mode
  const isRuleFiltering = !!filters.enhancement_rule_id

  // Load data on mount with initial filters from URL
  useEffect(() => {
    fetchTransactions({
      ...filters,
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
        fetchTransactions(updatedFilters)
      }
    }, 500) // 500ms debounce

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [localDescriptionSearch, localMinAmount, localMaxAmount, localStartDate, localEndDate, filters, fetchTransactions])

  const handleFilterChange = useCallback(
    (newFilters: Partial<FilterType>) => {
      const updatedFilters = {
        ...filters,
        ...newFilters,
        page: 1,
        include_running_balance: !!newFilters.source_id,
      } // Reset to first page when filters change
      setFilters(updatedFilters)
      fetchTransactions(updatedFilters)
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
      fetchTransactions(updatedFilters)
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
      fetchTransactions(updatedFilters)
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

  const handleStatusFilter = useCallback(
    (status?: CategorizationStatus) => {
      handleFilterChange({ status })
    },
    [handleFilterChange]
  )

  const handleAccountFilter = useCallback(
    (accountId?: string) => {
      handleFilterChange({ account_id: accountId })
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
    setLocalStartDate(startDate || '')
    setLocalEndDate(endDate || '')
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

  const handleCategorizeTransaction = async (transactionId: string, categoryId?: string) => {
    await categorizeTransaction(transactionId, categoryId)
    // Refresh the current page after categorization
    fetchTransactions({ ...filters, include_running_balance: !!filters.account_id })
  }

  return (
    <div className="transactions-page">
      <header className="page-header">
        <h1>Transactions</h1>
        <p className="page-description">
          View and manage your bank transactions with advanced filtering and categorization
        </p>
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
              selectedStatus={filters.status}
              selectedAccountId={filters.account_id}
              minAmount={localMinAmount}
              maxAmount={localMaxAmount}
              descriptionSearch={localDescriptionSearch}
              startDate={localStartDate}
              endDate={localEndDate}
              onCategoryChange={handleCategoryFilter}
              onStatusChange={handleStatusFilter}
              onAccountChange={handleAccountFilter}
              onAmountRangeChange={handleAmountRangeFilter}
              onDescriptionSearchChange={handleDescriptionSearchFilter}
              onDateRangeChange={handleDateRangeFilter}
              onClearFilters={handleClearFilters}
            />
          </div>
        )}

        <div className="transactions-content">
          <div className="transactions-header">
            <div className="transactions-summary">
              <h2>Transaction History</h2>
              {!loading && <span className="transaction-count">{pagination.total_count} transactions found</span>}
            </div>
          </div>

          <div className="transactions-table-container">
            <TransactionTable
              transactions={transactions || []}
              categories={categories || []}
              accounts={accounts || []}
              loading={loading}
              onCategorize={handleCategorizeTransaction}
              sortField={filters.sort_field as TransactionSortField}
              sortDirection={filters.sort_direction}
              onSort={handleSort}
              showRunningBalance={!!filters.account_id}
            />
          </div>

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
  )
}
