import { useState, useCallback } from 'react'
import { useApi } from '../../api/ApiContext'
import {
  TransactionCategorization,
  TransactionCategorizationCreate,
  TransactionCategorizationFilters,
  TransactionCategorizationStats,
  TransactionCategorizationUpdate,
} from '../../types/TransactionCategorization'

interface Pagination {
  current_page: number
  total_pages: number
  total_count: number
  page_size: number
}

export const useTransactionCategorizations = () => {
  const api = useApi()
  
  const [categorizations, setCategorizations] = useState<TransactionCategorization[]>([])
  const [stats, setStats] = useState<TransactionCategorizationStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [pagination, setPagination] = useState<Pagination>({
    current_page: 1,
    total_pages: 1,
    total_count: 0,
    page_size: 20,
  })

  const fetchCategorizations = useCallback(
    async (filters: TransactionCategorizationFilters = {}) => {
      setLoading(true)
      setError('')
      
      try {
        const response = await api.transactionCategorizations.getAll(filters)
        setCategorizations(response.categorizations)
        
        // Calculate pagination
        const page = filters.page || 1
        const pageSize = filters.page_size || 20
        const totalPages = Math.ceil(response.total / pageSize)
        
        setPagination({
          current_page: page,
          total_pages: totalPages,
          total_count: response.total,
          page_size: pageSize,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch categorizations')
        setCategorizations([])
        setPagination({
          current_page: 1,
          total_pages: 1,
          total_count: 0,
          page_size: 20,
        })
      } finally {
        setLoading(false)
      }
    },
    [api.transactionCategorizations]
  )

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError('')
    
    try {
      const statsData = await api.transactionCategorizations.getStats()
      setStats(statsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics')
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [api.transactionCategorizations])

  const createCategorization = useCallback(
    async (data: TransactionCategorizationCreate): Promise<TransactionCategorization> => {
      setLoading(true)
      setError('')
      
      try {
        const newCategorization = await api.transactionCategorizations.create(data)
        // Refresh the list to include the new categorization
        return newCategorization
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create categorization')
        throw err
      } finally {
        setLoading(false)
      }
    },
    [api.transactionCategorizations]
  )

  const updateCategorization = useCallback(
    async (id: string, data: TransactionCategorizationUpdate): Promise<TransactionCategorization> => {
      setLoading(true)
      setError('')
      
      try {
        const updatedCategorization = await api.transactionCategorizations.update(id, data)
        // Update the local state
        setCategorizations(prev => 
          prev.map(cat => cat.id === id ? updatedCategorization : cat)
        )
        return updatedCategorization
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update categorization')
        throw err
      } finally {
        setLoading(false)
      }
    },
    [api.transactionCategorizations]
  )

  const deleteCategorization = useCallback(
    async (id: string): Promise<void> => {
      setLoading(true)
      setError('')
      
      try {
        await api.transactionCategorizations.delete(id)
        // Remove from local state
        setCategorizations(prev => prev.filter(cat => cat.id !== id))
        // Update pagination count
        setPagination(prev => ({
          ...prev,
          total_count: Math.max(0, prev.total_count - 1),
        }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete categorization')
        throw err
      } finally {
        setLoading(false)
      }
    },
    [api.transactionCategorizations]
  )

  const cleanupUnusedRules = useCallback(async () => {
    setLoading(true)
    setError('')
    
    try {
      const result = await api.transactionCategorizations.cleanupUnused()
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup unused rules')
      throw err
    } finally {
      setLoading(false)
    }
  }, [api.transactionCategorizations])

  return {
    categorizations,
    stats,
    loading,
    error,
    pagination,
    fetchCategorizations,
    fetchStats,
    createCategorization,
    updateCategorization,
    deleteCategorization,
    cleanupUnusedRules,
  }
}