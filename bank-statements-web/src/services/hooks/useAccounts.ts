import { useState, useEffect, useCallback } from 'react'
import { Account } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'

export const useAccounts = () => {
  const api = useApi()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAccounts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.accounts.getAll()
      setAccounts(response)
    } catch (err) {
      console.error('Error fetching accounts:', err)
      setError('Failed to fetch accounts. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.accounts])

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  return {
    accounts,
    loading,
    error,
    fetchAccounts,
  }
}
