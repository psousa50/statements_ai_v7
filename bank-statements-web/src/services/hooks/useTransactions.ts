import { useState, useEffect, useCallback } from 'react'
import { CategorizationStatus, Transaction, TransactionCreate } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'

export const useTransactions = () => {
  const api = useApi()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTransactions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.transactions.getAll()
      setTransactions(response.transactions)
    } catch (err) {
      console.error('Error fetching transactions:', err)
      setError('Failed to fetch transactions. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.transactions])

  const addTransaction = useCallback(
    async (transaction: TransactionCreate) => {
      setLoading(true)
      setError(null)
      try {
        const newTransaction = await api.transactions.create(transaction)
        setTransactions((prev) => [...prev, newTransaction])
        return newTransaction
      } catch (err) {
        console.error('Error adding transaction:', err)
        setError('Failed to add transaction. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.transactions]
  )

  const updateTransaction = useCallback(
    async (id: string, transaction: TransactionCreate) => {
      setLoading(true)
      setError(null)
      try {
        const updatedTransaction = await api.transactions.update(id, transaction)
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
        // In a real app, we'd have a dedicated endpoint for this
        const transaction = transactions.find((t) => t.id === id)
        if (!transaction) {
          throw new Error(`Transaction with ID ${id} not found`)
        }

        const updatedTransaction = await api.transactions.update(id, {
          date: transaction.date,
          description: transaction.description,
          amount: transaction.amount,
          category_id: categoryId,
        })

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
    [api.transactions, transactions]
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
    fetchTransactions,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    categorizeTransaction,
    getTransactionsByCategory,
    getTransactionsByStatus,
  }
}
