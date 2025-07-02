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

  const addAccount = useCallback(
    async (name: string) => {
      try {
        const newAccount = await api.accounts.createAccount(name)
        setAccounts((prev) => [...prev, newAccount].sort((a, b) => a.name.localeCompare(b.name)))
        return newAccount
      } catch (err) {
        console.error('Error creating account:', err)
        setError('Failed to create account. Please try again.')
        return null
      }
    },
    [api.accounts]
  )

  const updateAccount = useCallback(
    async (id: string, name: string) => {
      try {
        const updatedAccount = await api.accounts.updateAccount(id, name)
        setAccounts((prev) =>
          prev
            .map((account) => (account.id === id ? updatedAccount : account))
            .sort((a, b) => a.name.localeCompare(b.name))
        )
        return updatedAccount
      } catch (err) {
        console.error('Error updating account:', err)
        setError('Failed to update account. Please try again.')
        return null
      }
    },
    [api.accounts]
  )

  const deleteAccount = useCallback(
    async (id: string) => {
      try {
        await api.accounts.deleteAccount(id)
        setAccounts((prev) => prev.filter((account) => account.id !== id))
        return true
      } catch (err) {
        console.error('Error deleting account:', err)
        setError('Failed to delete account. Please try again.')
        return false
      }
    },
    [api.accounts]
  )

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  return {
    accounts,
    loading,
    error,
    fetchAccounts,
    addAccount,
    updateAccount,
    deleteAccount,
  }
}
