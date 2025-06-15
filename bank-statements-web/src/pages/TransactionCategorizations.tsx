import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTransactionCategorizations } from '../services/hooks/useTransactionCategorizations'
import { useCategories } from '../services/hooks/useCategories'
import { useApi } from '../api/ApiContext'
import { TransactionCategorizationTable } from '../components/TransactionCategorizationTable'
import { TransactionCategorizationFilters } from '../components/TransactionCategorizationFilters'
import { EditCategorizationModal } from '../components/EditCategorizationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Pagination } from '../components/Pagination'
import {
  CategorizationSource,
  TransactionCategorizationFilters as FilterType,
  SortField,
  SortDirection,
  TransactionCategorization,
} from '../types/TransactionCategorization'
import './TransactionCategorizationsPage.css'

export const TransactionCategorizationsPage = () => {
  const navigate = useNavigate()
  const api = useApi()
  const [filters, setFilters] = useState<FilterType>({
    page: 1,
    page_size: 20,
  })
  const [editingCategorization, setEditingCategorization] = useState<TransactionCategorization | null>(null)
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)

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
    updateCategorization,
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

  const handleSort = useCallback(
    (field: SortField) => {
      let newDirection: SortDirection = 'asc'

      // If clicking the same field, toggle direction
      if (filters.sort_field === field) {
        newDirection = filters.sort_direction === 'asc' ? 'desc' : 'asc'
      }

      const updatedFilters = {
        ...filters,
        sort_field: field,
        sort_direction: newDirection,
        page: 1, // Reset to first page when sorting
      }

      setFilters(updatedFilters)
      fetchCategorizations(updatedFilters)
    },
    [filters, fetchCategorizations]
  )

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

  const handleViewTransactions = useCallback(
    (description: string) => {
      const searchParams = new URLSearchParams()
      searchParams.set('description_search', description)
      navigate(`/transactions?${searchParams.toString()}`)
    },
    [navigate]
  )

  const handleEditCategorization = useCallback((categorization: TransactionCategorization) => {
    setEditingCategorization(categorization)
  }, [])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

  const handleSaveEdit = useCallback(
    async (
      id: string,
      updates: {
        normalized_description: string
        category_id: string
        source: CategorizationSource
      },
      applyToAllSame: boolean
    ) => {
      try {
        // Validate that we have a valid category_id
        if (!updates.category_id || updates.category_id === '') {
          throw new Error('Category is required')
        }
        
        await updateCategorization(id, updates)

        // Check if we need to perform bulk update (only if category actually changed)
        const oldCategoryId = editingCategorization?.category_id || ''
        const newCategoryId = updates.category_id || ''
        const categoryActuallyChanged = newCategoryId !== oldCategoryId
        
        if (applyToAllSame && categoryActuallyChanged) {
          // Perform bulk update for all transactions with same description
          const normalizedDesc = editingCategorization?.normalized_description || ''
          const bulkUpdateRequest = {
            normalized_description: normalizedDesc,
            category_id: updates.category_id && updates.category_id !== '' ? updates.category_id : undefined,
          }
          
          // Validate the request before sending
          if (normalizedDesc.length < 2) {
            throw new Error('Normalized description is too short for bulk update')
          }
          
          const bulkUpdateResult = await api.transactions.bulkUpdateCategory(bulkUpdateRequest)
          
          // Show success toast
          setToast({
            message: `Successfully updated ${bulkUpdateResult.updated_count} transactions`,
            type: 'success'
          })
        }

        // Refresh data
        fetchCategorizations(filters)
        fetchStats()
        setEditingCategorization(null)
      } catch (error) {
        console.error('Failed to update categorization:', error)
        setToast({
          message: 'Failed to update categorization. Please try again.',
          type: 'error'
        })
        // Don't re-throw the error to prevent modal from staying open
      }
    },
    [updateCategorization, editingCategorization, fetchCategorizations, fetchStats, filters]
  )

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
            sortField={filters.sort_field}
            sortDirection={filters.sort_direction}
            onEdit={handleEditCategorization}
            onDelete={handleDeleteCategorization}
            onViewTransactions={handleViewTransactions}
            onSort={handleSort}
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

      <EditCategorizationModal
        categorization={editingCategorization}
        categories={categories || []}
        isOpen={!!editingCategorization}
        onClose={() => setEditingCategorization(null)}
        onSave={handleSaveEdit}
      />

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={handleCloseToast}
        />
      )}
    </div>
  )
}
