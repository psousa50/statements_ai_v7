import { useState, useCallback, useEffect, useRef } from 'react'
import { useTransactions } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { useSources } from '../services/hooks/useSources'
import { TransactionTable } from '../components/TransactionTable'
import { TransactionFilters } from '../components/TransactionFilters'
import { Pagination } from '../components/Pagination'
import { CategorizationStatus } from '../types/Transaction'
import { TransactionFilters as FilterType } from '../api/TransactionClient'
import './TransactionsPage.css'

export const TransactionsPage = () => {
  const [filters, setFilters] = useState<FilterType>({
    page: 1,
    page_size: 20,
  })

  // Local state for debounced inputs
  const [localDescriptionSearch, setLocalDescriptionSearch] = useState<string>('')
  const [localMinAmount, setLocalMinAmount] = useState<number | undefined>()
  const [localMaxAmount, setLocalMaxAmount] = useState<number | undefined>()
  const [localStartDate, setLocalStartDate] = useState<string>('')
  const [localEndDate, setLocalEndDate] = useState<string>('')

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    transactions,
    loading: transactionsLoading,
    error: transactionsError,
    pagination,
    fetchTransactions,
    categorizeTransaction,
  } = useTransactions()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()
  const { sources, loading: sourcesLoading, error: sourcesError } = useSources()

  const loading = transactionsLoading || categoriesLoading || sourcesLoading
  const error = transactionsError || categoriesError || sourcesError

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
      const updatedFilters = { ...filters, ...newFilters, page: 1 } // Reset to first page when filters change
      setFilters(updatedFilters)
      fetchTransactions(updatedFilters)
    },
    [filters, fetchTransactions]
  )

  const handlePageChange = useCallback(
    (page: number) => {
      const updatedFilters = { ...filters, page }
      setFilters(updatedFilters)
      fetchTransactions(updatedFilters)
    },
    [filters, fetchTransactions]
  )

  const handlePageSizeChange = useCallback(
    (page_size: number) => {
      const updatedFilters = { ...filters, page_size, page: 1 }
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

  const handleSourceFilter = useCallback(
    (sourceId?: string) => {
      handleFilterChange({ source_id: sourceId })
    },
    [handleFilterChange]
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
    const clearedFilters = { page: 1, page_size: filters.page_size }
    setFilters(clearedFilters)
    setLocalDescriptionSearch('')
    setLocalMinAmount(undefined)
    setLocalMaxAmount(undefined)
    setLocalStartDate('')
    setLocalEndDate('')
    fetchTransactions(clearedFilters)
  }, [filters.page_size, fetchTransactions])

  const handleCategorizeTransaction = async (transactionId: string, categoryId?: string) => {
    await categorizeTransaction(transactionId, categoryId)
    // Refresh the current page after categorization
    fetchTransactions(filters)
  }

  return (
    <div className="transactions-page">
      <header className="page-header">
        <h1>Transactions</h1>
        <p className="page-description">
          View and manage your bank transactions with advanced filtering and categorization
        </p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="transactions-layout">
        <div className="filters-sidebar">
          <TransactionFilters
            categories={categories || []}
            sources={sources || []}
            selectedCategoryIds={filters.category_ids}
            selectedStatus={filters.status}
            selectedSourceId={filters.source_id}
            minAmount={localMinAmount}
            maxAmount={localMaxAmount}
            descriptionSearch={localDescriptionSearch}
            startDate={localStartDate}
            endDate={localEndDate}
            onCategoryChange={handleCategoryFilter}
            onStatusChange={handleStatusFilter}
            onSourceChange={handleSourceFilter}
            onAmountRangeChange={handleAmountRangeFilter}
            onDescriptionSearchChange={handleDescriptionSearchFilter}
            onDateRangeChange={handleDateRangeFilter}
            onClearFilters={handleClearFilters}
          />
        </div>

        <div className="transactions-content">
          <div className="transactions-header">
            <div className="transactions-summary">
              <h2>Transaction History</h2>
              {!loading && <span className="transaction-count">{pagination.total} transactions found</span>}
            </div>
          </div>

          <div className="transactions-table-container">
            <TransactionTable
              transactions={transactions || []}
              categories={categories || []}
              sources={sources || []}
              loading={loading}
              onCategorize={handleCategorizeTransaction}
            />
          </div>

          {!loading && pagination.total > 0 && (
            <div className="transactions-pagination">
              <Pagination
                currentPage={pagination.page}
                totalPages={pagination.totalPages}
                totalItems={pagination.total}
                pageSize={pagination.pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
