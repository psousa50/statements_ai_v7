import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CategorizationStatus, Transaction } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'
import {
  TransactionFilters,
  CategoryTotalsResponse,
  CategoryTimeSeriesDataPoint,
  RecurringPatternsResponse,
} from '../../api/TransactionClient'
import { EnhancementRule } from '../../types/EnhancementRule'
import { CATEGORY_QUERY_KEYS } from './useCategories'

interface TransactionPagination {
  current_page: number
  total_pages: number
  page_size: number
  total_count: number
  total_amount: number
}

export const TRANSACTION_QUERY_KEYS = {
  all: ['transactions'] as const,
  list: (filters?: TransactionFilters) => ['transactions', 'list', filters] as const,
  categoryTotals: (filters?: object) => ['transactions', 'categoryTotals', filters] as const,
  timeSeries: (categoryId?: string, period?: string, filters?: object) =>
    ['transactions', 'timeSeries', categoryId, period, filters] as const,
  recurringPatterns: (activeOnly?: boolean) => ['transactions', 'recurringPatterns', activeOnly] as const,
}

export const useTransactions = () => {
  const api = useApi()
  const queryClient = useQueryClient()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [enhancementRule, setEnhancementRule] = useState<EnhancementRule | null>(null)
  const [pagination, setPagination] = useState<TransactionPagination>({
    current_page: 1,
    total_pages: 1,
    page_size: 20,
    total_count: 0,
    total_amount: 0,
  })

  const fetchTransactions = useCallback(
    async (filters?: TransactionFilters) => {
      setLoading(true)
      setError(null)
      try {
        const cacheKey = TRANSACTION_QUERY_KEYS.list(filters)
        const queryState = queryClient.getQueryState(cacheKey)
        const cached = queryClient.getQueryData<{
          transactions: Transaction[]
          total: number
          total_amount: number
          enhancement_rule?: EnhancementRule
        }>(cacheKey)

        let response
        const isStale = queryState?.isInvalidated || !queryState
        if (cached && !isStale) {
          response = cached
        } else {
          response = await api.transactions.getAll(filters)
          queryClient.setQueryData(cacheKey, response)
        }

        setTransactions(response.transactions)
        setEnhancementRule(response.enhancement_rule || null)

        const pageSize = filters?.page_size || 20
        const currentPage = filters?.page || 1
        const totalPages = Math.ceil(response.total / pageSize)

        setPagination({
          current_page: currentPage,
          total_pages: totalPages,
          page_size: pageSize,
          total_count: response.total,
          total_amount: response.total_amount ?? 0,
        })
      } catch (err) {
        console.error('Error fetching transactions:', err)
        setError('Failed to fetch transactions. Please try again later.')
      } finally {
        setLoading(false)
      }
    },
    [api.transactions, queryClient]
  )

  const addMutation = useMutation({
    mutationFn: async (transactionData: {
      date: string
      description: string
      amount: number
      account_id: string
      category_id?: string
      counterparty_account_id?: string
    }) => {
      return api.transactions.create(transactionData)
    },
    onSuccess: (newTransaction) => {
      setTransactions((prev) => [newTransaction, ...prev])
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string
      data: {
        date: string
        description: string
        amount: number
        account_id: string
        category_id?: string
        counterparty_account_id?: string
      }
    }) => {
      return api.transactions.update(id, data)
    },
    onSuccess: (updatedTransaction) => {
      setTransactions((prev) => prev.map((t) => (t.id === updatedTransaction.id ? updatedTransaction : t)))
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.transactions.delete(id)
      return id
    },
    onSuccess: (deletedId) => {
      setTransactions((prev) => prev.filter((t) => t.id !== deletedId))
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const categorizeMutation = useMutation({
    mutationFn: async ({ id, categoryId }: { id: string; categoryId?: string }) => {
      return api.transactions.categorize(id, categoryId)
    },
    onSuccess: (updatedTransaction) => {
      setTransactions((prev) => prev.map((t) => (t.id === updatedTransaction.id ? updatedTransaction : t)))
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
    },
  })

  const bulkUpdateCategoryMutation = useMutation({
    mutationFn: async (params: {
      normalized_description: string
      category_id: string
      account_id?: string
      start_date?: string
      end_date?: string
      exclude_transfers?: boolean
      enhancement_rule_id?: string
    }) => {
      return api.transactions.bulkUpdateCategory(params)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const bulkReplaceCategoryMutation = useMutation({
    mutationFn: async (params: {
      from_category_id: string
      to_category_id: string
      account_id?: string
      start_date?: string
      end_date?: string
      exclude_transfers?: boolean
    }) => {
      return api.transactions.bulkReplaceCategory(params)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const addTransaction = useCallback(
    async (transactionData: {
      date: string
      description: string
      amount: number
      account_id: string
      category_id?: string
      counterparty_account_id?: string
    }) => {
      try {
        return await addMutation.mutateAsync(transactionData)
      } catch {
        setError('Failed to create transaction. Please try again later.')
        return null
      }
    },
    [addMutation]
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
      try {
        return await updateMutation.mutateAsync({ id, data: transactionData })
      } catch {
        setError('Failed to update transaction. Please try again later.')
        return null
      }
    },
    [updateMutation]
  )

  const deleteTransaction = useCallback(
    async (id: string) => {
      try {
        await deleteMutation.mutateAsync(id)
        return true
      } catch {
        setError('Failed to delete transaction. Please try again later.')
        return false
      }
    },
    [deleteMutation]
  )

  const categorizeTransaction = useCallback(
    async (id: string, categoryId?: string) => {
      try {
        return await categorizeMutation.mutateAsync({ id, categoryId })
      } catch {
        setError('Failed to categorize transaction. Please try again later.')
        return null
      }
    },
    [categorizeMutation]
  )

  const bulkUpdateCategory = useCallback(
    async (
      normalizedDescription: string,
      categoryId: string,
      filterOptions?: {
        account_id?: string
        start_date?: string
        end_date?: string
        exclude_transfers?: boolean
        enhancement_rule_id?: string
      }
    ) => {
      try {
        return await bulkUpdateCategoryMutation.mutateAsync({
          normalized_description: normalizedDescription,
          category_id: categoryId,
          ...filterOptions,
        })
      } catch {
        setError('Failed to apply category to similar transactions.')
        return null
      }
    },
    [bulkUpdateCategoryMutation]
  )

  const bulkReplaceCategory = useCallback(
    async (
      fromCategoryId: string,
      toCategoryId: string,
      filterOptions?: {
        account_id?: string
        start_date?: string
        end_date?: string
        exclude_transfers?: boolean
      }
    ) => {
      try {
        return await bulkReplaceCategoryMutation.mutateAsync({
          from_category_id: fromCategoryId,
          to_category_id: toCategoryId,
          ...filterOptions,
        })
      } catch {
        setError('Failed to replace category for transactions.')
        return null
      }
    },
    [bulkReplaceCategoryMutation]
  )

  const getTransactionsByCategory = useCallback(
    (categoryId?: string) => {
      if (!categoryId) return transactions
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

  const isLoading =
    loading ||
    addMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    categorizeMutation.isPending

  return {
    transactions,
    loading: isLoading,
    error,
    enhancementRule,
    pagination,
    fetchTransactions,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    categorizeTransaction,
    bulkUpdateCategory,
    bulkReplaceCategory,
    getTransactionsByCategory,
    getTransactionsByStatus,
  }
}

export const useCategoryTotals = () => {
  const api = useApi()
  const queryClient = useQueryClient()
  const [categoryTotals, setCategoryTotals] = useState<CategoryTotalsResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCategoryTotals = useCallback(
    async (filters?: Omit<TransactionFilters, 'page' | 'page_size'>) => {
      setLoading(true)
      setError(null)
      try {
        const cacheKey = TRANSACTION_QUERY_KEYS.categoryTotals(filters)
        const queryState = queryClient.getQueryState(cacheKey)
        const cached = queryClient.getQueryData<CategoryTotalsResponse>(cacheKey)

        let response
        const isStale = queryState?.isInvalidated || !queryState
        if (cached && !isStale) {
          response = cached
        } else {
          response = await api.transactions.getCategoryTotals(filters)
          queryClient.setQueryData(cacheKey, response)
        }

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
    [api.transactions, queryClient]
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
  const queryClient = useQueryClient()
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
        const cacheKey = TRANSACTION_QUERY_KEYS.timeSeries(categoryId, period, filters)
        const queryState = queryClient.getQueryState(cacheKey)
        const cached = queryClient.getQueryData<{ data_points: CategoryTimeSeriesDataPoint[] }>(cacheKey)

        let response
        const isStale = queryState?.isInvalidated || !queryState
        if (cached && !isStale) {
          response = cached
        } else {
          response = await api.transactions.getCategoryTimeSeries(categoryId, period, filters)
          queryClient.setQueryData(cacheKey, response)
        }

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
    [api.transactions, queryClient]
  )

  return {
    timeSeriesData,
    loading,
    error,
    fetchCategoryTimeSeries,
  }
}

export const useRecurringPatterns = () => {
  const api = useApi()
  const queryClient = useQueryClient()
  const [recurringPatterns, setRecurringPatterns] = useState<RecurringPatternsResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRecurringPatterns = useCallback(
    async (activeOnly: boolean = true) => {
      setLoading(true)
      setError(null)
      try {
        const cacheKey = TRANSACTION_QUERY_KEYS.recurringPatterns(activeOnly)
        const queryState = queryClient.getQueryState(cacheKey)
        const cached = queryClient.getQueryData<RecurringPatternsResponse>(cacheKey)

        let response
        const isStale = queryState?.isInvalidated || !queryState
        if (cached && !isStale) {
          response = cached
        } else {
          response = await api.transactions.getRecurringPatterns(activeOnly)
          queryClient.setQueryData(cacheKey, response)
        }

        setRecurringPatterns(response)
        return response
      } catch (err) {
        console.error('Error fetching recurring patterns:', err)
        setError('Failed to fetch recurring patterns. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions, queryClient]
  )

  return {
    recurringPatterns,
    loading,
    error,
    fetchRecurringPatterns,
  }
}
