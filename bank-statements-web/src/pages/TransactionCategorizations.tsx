import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTransactionCategorizations } from '../services/hooks/useTransactionCategorizations'
import { useCategories } from '../services/hooks/useCategories'
import { TransactionCategorizationTable } from '../components/TransactionCategorizationTable'
import { TransactionCategorizationFilters } from '../components/TransactionCategorizationFilters'
import { Pagination } from '../components/Pagination'
import {
  CategorizationSource,
  TransactionCategorizationFilters as FilterType,
} from '../types/TransactionCategorization'
import './TransactionCategorizationsPage.css'

export const TransactionCategorizationsPage = () => {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<FilterType>({
    page: 1,
    page_size: 20,
  })

  // Local state for debounced inputs
  const [localDescriptionSearch, setLocalDescriptionSearch] = useState<string>('')

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    categorizations,
    stats,
    loading: categorizationsLoading,
    error: categorizationsError,
    pagination,
    fetchCategorizations,
    fetchStats,
    deleteCategorization,
    cleanupUnusedRules,
  } = useTransactionCategorizations()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()

  const loading = categorizationsLoading || categoriesLoading
  const error = categorizationsError || categoriesError

  // Load data on mount
  useEffect(() => {
    fetchCategorizations(filters)
    fetchStats()
  }, [])

  // Debounced filter update for search
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = setTimeout(() => {
      const needsUpdate = localDescriptionSearch !== (filters.description_search || '')

      if (needsUpdate) {
        const updatedFilters = {
          ...filters,
          description_search: localDescriptionSearch || undefined,
          page: 1,
        }
        setFilters(updatedFilters)
        fetchCategorizations(updatedFilters)
      }
    }, 500) // 500ms debounce

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [localDescriptionSearch, filters, fetchCategorizations])

  const handleFilterChange = useCallback(
    (newFilters: Partial<FilterType>) => {
      const updatedFilters = { ...filters, ...newFilters, page: 1 } // Reset to first page when filters change
      setFilters(updatedFilters)
      fetchCategorizations(updatedFilters)
    },
    [filters, fetchCategorizations]
  )

  const handlePageChange = useCallback(
    (page: number) => {
      const updatedFilters = { ...filters, page }
      setFilters(updatedFilters)
      fetchCategorizations(updatedFilters)
    },
    [filters, fetchCategorizations]
  )

  const handlePageSizeChange = useCallback(
    (page_size: number) => {
      const updatedFilters = { ...filters, page_size, page: 1 }
      setFilters(updatedFilters)
      fetchCategorizations(updatedFilters)
    },
    [filters, fetchCategorizations]
  )

  // Immediate updates (no debouncing needed)
  const handleCategoryFilter = useCallback(
    (categoryIds: string[]) => {
      handleFilterChange({ category_ids: categoryIds })
    },
    [handleFilterChange]
  )

  const handleSourceFilter = useCallback(
    (source?: CategorizationSource) => {
      handleFilterChange({ source })
    },
    [handleFilterChange]
  )

  // Debounced updates (local state only)
  const handleDescriptionSearchFilter = useCallback((search?: string) => {
    setLocalDescriptionSearch(search || '')
  }, [])

  const handleClearFilters = useCallback(() => {
    const clearedFilters = { page: 1, page_size: filters.page_size }
    setFilters(clearedFilters)
    setLocalDescriptionSearch('')
    fetchCategorizations(clearedFilters)
  }, [filters.page_size, fetchCategorizations])

  const handleDeleteCategorization = async (id: string) => {
    try {
      await deleteCategorization(id)
      // Refresh stats after deletion
      fetchStats()
    } catch (error) {
      console.error('Failed to delete categorization:', error)
    }
  }

  const handleCleanupUnused = async () => {
    if (
      !window.confirm('Are you sure you want to delete all unused categorization rules? This action cannot be undone.')
    ) {
      return
    }

    try {
      const result = await cleanupUnusedRules()
      alert(`Successfully cleaned up ${result.deleted_count} unused rules.`)

      // Refresh data after cleanup
      fetchCategorizations(filters)
      fetchStats()
    } catch (error) {
      console.error('Failed to cleanup unused rules:', error)
      alert('Failed to cleanup unused rules. Please try again.')
    }
  }

  const handleViewTransactions = useCallback((description: string) => {
    const searchParams = new URLSearchParams()
    searchParams.set('description_search', description)
    navigate(`/transactions?${searchParams.toString()}`)
  }, [navigate])

  return (
    <div className="transaction-categorizations-page">
      <header className="page-header">
        <h1>Transaction Categorization Management</h1>
        <p className="page-description">Manage your transaction categorization rules and view usage statistics</p>
      </header>

      {/* Summary Cards */}
      {stats && (
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-value">{stats.summary.total_rules}</div>
            <div className="card-label">Total Rules</div>
          </div>
          <div className="summary-card">
            <div className="card-value">{stats.summary.manual_rules}</div>
            <div className="card-label">Manual Rules</div>
          </div>
          <div className="summary-card">
            <div className="card-value">{stats.summary.ai_rules}</div>
            <div className="card-label">AI Rules</div>
          </div>
          <div className="summary-card">
            <div className="card-value">{stats.summary.total_transactions_categorized.toLocaleString()}</div>
            <div className="card-label">Transactions Covered</div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="filters-top">
        <TransactionCategorizationFilters
          categories={categories || []}
          selectedCategoryIds={filters.category_ids}
          selectedSource={filters.source}
          descriptionSearch={localDescriptionSearch}
          onCategoryChange={handleCategoryFilter}
          onSourceChange={handleSourceFilter}
          onDescriptionSearchChange={handleDescriptionSearchFilter}
          onClearFilters={handleClearFilters}
        />
      </div>

      <div className="categorizations-content">
        <div className="categorizations-header">
          <div className="categorizations-summary">
            <h2>Categorization Rules</h2>
            {!loading && <span className="categorization-count">{pagination.total_count} rules found</span>}
          </div>

          <div className="categorizations-actions">
            {stats && stats.unused_rules.length > 0 && (
              <button
                onClick={handleCleanupUnused}
                className="cleanup-button"
                title={`Delete ${stats.unused_rules.length} unused rules`}
              >
                🧹 Cleanup Unused ({stats.unused_rules.length})
              </button>
            )}
            <button onClick={() => fetchStats()} className="refresh-button" title="Refresh statistics">
              📊 Refresh Stats
            </button>
          </div>
        </div>

        {!loading && pagination.total_count > 0 && (
          <div className="categorizations-pagination-top">
            <Pagination
              currentPage={pagination.current_page}
              totalPages={pagination.total_pages}
              totalItems={pagination.total_count}
              pageSize={pagination.page_size}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </div>
        )}

        <div className="categorizations-table-container">
          <TransactionCategorizationTable
            categorizations={categorizations || []}
            categories={categories || []}
            loading={loading}
            onDelete={handleDeleteCategorization}
            onViewTransactions={handleViewTransactions}
          />
        </div>

        {!loading && pagination.total_count > 0 && (
          <div className="categorizations-pagination">
            <Pagination
              currentPage={pagination.current_page}
              totalPages={pagination.total_pages}
              totalItems={pagination.total_count}
              pageSize={pagination.page_size}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </div>
        )}
      </div>
    </div>
  )
}
