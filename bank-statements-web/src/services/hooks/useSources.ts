import { useState, useEffect, useCallback } from 'react'
import { Source } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'

export const useSources = () => {
  const api = useApi()
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSources = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.sources.getAll()
      setSources(response)
    } catch (err) {
      console.error('Error fetching sources:', err)
      setError('Failed to fetch sources. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.sources])

  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  return {
    sources,
    loading,
    error,
    fetchSources,
  }
}
