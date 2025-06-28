import { useState, useCallback } from 'react'
import { useApi } from '../../api/ApiContext'
import {
  EnhancementRule,
  EnhancementRuleCreate,
  EnhancementRuleFilters,
  EnhancementRuleStats,
  EnhancementRuleUpdate,
} from '../../types/EnhancementRule'

export const useEnhancementRules = () => {
  const apiClient = useApi()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRules = useCallback(
    async (filters?: EnhancementRuleFilters) => {
      setLoading(true)
      setError(null)
      try {
        const response = await apiClient.enhancementRules.getAll(filters)
        return response
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch enhancement rules'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiClient]
  )

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const stats = await apiClient.enhancementRules.getStats()
      return stats
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch enhancement rule stats'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiClient])

  const fetchRule = useCallback(
    async (id: string) => {
      setLoading(true)
      setError(null)
      try {
        const rule = await apiClient.enhancementRules.getById(id)
        return rule
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch enhancement rule'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiClient]
  )

  const createRule = useCallback(
    async (data: EnhancementRuleCreate) => {
      setLoading(true)
      setError(null)
      try {
        const rule = await apiClient.enhancementRules.create(data)
        return rule
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create enhancement rule'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiClient]
  )

  const updateRule = useCallback(
    async (id: string, data: EnhancementRuleUpdate) => {
      setLoading(true)
      setError(null)
      try {
        const rule = await apiClient.enhancementRules.update(id, data)
        return rule
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update enhancement rule'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiClient]
  )

  const deleteRule = useCallback(
    async (id: string) => {
      setLoading(true)
      setError(null)
      try {
        await apiClient.enhancementRules.delete(id)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete enhancement rule'
        setError(errorMessage)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiClient]
  )

  const cleanupUnused = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.enhancementRules.cleanupUnused()
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cleanup unused rules'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiClient])

  return {
    loading,
    error,
    fetchRules,
    fetchStats,
    fetchRule,
    createRule,
    updateRule,
    deleteRule,
    cleanupUnused,
  }
}
