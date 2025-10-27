import { useState, useEffect, useCallback } from 'react'
import { CategorizationStatus, Transaction } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'
import { TransactionFilters, CategoryTotalsResponse, CategoryTimeSeriesDataPoint } from '../../api/TransactionClient'
import { EnhancementRule } from '../../types/EnhancementRule'

interface TransactionPagination {
  current_page: number
  total_pages: number
  page_size: number
  total_count: number
}

export const useTransactions = () => {
  const api = useApi()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [enhancementRule, setEnhancementRule] = useState<EnhancementRule | null>(null)
  const [pagination, setPagination] = useState<TransactionPagination>({
    current_page: 1,
    total_pages: 1,
    page_size: 20,
    total_count: 0,
  })

  const fetchTransactions = useCallback(
    async (filters?: TransactionFilters) => {
      setLoading(true)
      setError(null)
      try {
        const response = await api.transactions.getAll(filters)
        setTransactions(response.transactions)
        setEnhancementRule(response.enhancement_rule || null)

        // Calculate pagination from response
        const pageSize = filters?.page_size || 20
        const currentPage = filters?.page || 1
        const totalPages = Math.ceil(response.total / pageSize)

        setPagination({
          current_page: currentPage,
          total_pages: totalPages,
          page_size: pageSize,
          total_count: response.total,
        })
      } catch (err) {
        console.error('Error fetching transactions:', err)
        setError('Failed to fetch transactions. Please try again later.')
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const addTransaction = useCallback(
    async (transactionData: {
      date: string
      description: string
      amount: number
      account_id: string
      category_id?: string
      counterparty_account_id?: string
    }) => {
      setLoading(true)
      setError(null)
      try {
        const newTransaction = await api.transactions.create(transactionData)
        setTransactions((prev) => [newTransaction, ...prev])
        return newTransaction
      } catch (err) {
        console.error('Error creating transaction:', err)
        setError('Failed to create transaction. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const updateTransaction = useCallback(
    async (
      id: string,
      transactionData: {
        date: string
        description: string
        amount: number
        account_id: string
        category_id?: string
        counterparty_account_id?: string
      }
    ) => {
      setLoading(true)
      setError(null)
      try {
        const updatedTransaction = await api.transactions.update(id, transactionData)
        setTransactions((prev) => prev.map((t) => (t.id === id ? updatedTransaction : t)))
        return updatedTransaction
      } catch (err) {
        console.error('Error updating transaction:', err)
        setError('Failed to update transaction. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const deleteTransaction = useCallback(
    async (id: string) => {
      setLoading(true)
      setError(null)
      try {
        await api.transactions.delete(id)
        setTransactions((prev) => prev.filter((t) => t.id !== id))
        return true
      } catch (err) {
        console.error('Error deleting transaction:', err)
        setError('Failed to delete transaction. Please try again later.')
        return false
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const categorizeTransaction = useCallback(
    async (id: string, categoryId?: string) => {
      setLoading(true)
      setError(null)
      try {
        const updatedTransaction = await api.transactions.categorize(id, categoryId)

        setTransactions((prev) => prev.map((t) => (t.id === id ? updatedTransaction : t)))

        return updatedTransaction
      } catch (err) {
        console.error('Error categorizing transaction:', err)
        setError('Failed to categorize transaction. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const getTransactionsByCategory = useCallback(
    (categoryId?: string) => {
      if (!categoryId) {
        return transactions
      }
      return transactions.filter((t) => t.category_id === categoryId)
    },
    [transactions]
  )

  const getTransactionsByStatus = useCallback(
    (status: CategorizationStatus) => {
      return transactions.filter((t) => t.categorization_status === status)
    },
    [transactions]
  )

  useEffect(() => {
    fetchTransactions()
  }, [fetchTransactions])

  return {
    transactions,
    loading,
    error,
    enhancementRule,
    pagination,
    fetchTransactions,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    categorizeTransaction,
    getTransactionsByCategory,
    getTransactionsByStatus,
  }
}

export const useCategoryTotals = () => {
  const api = useApi()
  const [categoryTotals, setCategoryTotals] = useState<CategoryTotalsResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCategoryTotals = useCallback(
    async (filters?: Omit<TransactionFilters, 'page' | 'page_size'>) => {
      setLoading(true)
      setError(null)
      try {
        const response = await api.transactions.getCategoryTotals(filters)
        setCategoryTotals(response)
        return response
      } catch (err) {
        console.error('Error fetching category totals:', err)
        setError('Failed to fetch category totals. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  return {
    categoryTotals,
    loading,
    error,
    fetchCategoryTotals,
  }
}

export const useCategoryTimeSeries = () => {
  const api = useApi()
  const [timeSeriesData, setTimeSeriesData] = useState<CategoryTimeSeriesDataPoint[] | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCategoryTimeSeries = useCallback(
    async (
      categoryId?: string,
      period: 'month' | 'week' = 'month',
      filters?: Omit<TransactionFilters, 'page' | 'page_size'>
    ) => {
      setLoading(true)
      setError(null)
      try {
        const response = await api.transactions.getCategoryTimeSeries(categoryId, period, filters)
        setTimeSeriesData(response.data_points)
        return response.data_points
      } catch (err) {
        console.error('Error fetching category time series:', err)
        setError('Failed to fetch time series data. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  return {
    timeSeriesData,
    loading,
    error,
    fetchCategoryTimeSeries,
  }
}
