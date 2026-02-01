import { useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Account } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'
import { getErrorMessage } from '../../types/ApiError'

const sortByName = (accounts: Account[]) => [...accounts].sort((a, b) => a.name.localeCompare(b.name))

export const ACCOUNT_QUERY_KEYS = {
  all: ['accounts'] as const,
}

export const useAccounts = () => {
  const api = useApi()
  const queryClient = useQueryClient()

  const accountsQuery = useQuery({
    queryKey: ACCOUNT_QUERY_KEYS.all,
    queryFn: async () => {
      const response = await api.accounts.getAll()
      return sortByName(response)
    },
  })

  const addMutation = useMutation({
    mutationFn: async ({ name, currency }: { name: string; currency: string }) => {
      return api.accounts.createAccount(name, currency)
    },
    onSuccess: (newAccount) => {
      queryClient.setQueryData<Account[]>(ACCOUNT_QUERY_KEYS.all, (old) => sortByName([...(old ?? []), newAccount]))
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, name, currency }: { id: string; name: string; currency: string }) => {
      return api.accounts.updateAccount(id, name, currency)
    },
    onSuccess: (updatedAccount) => {
      queryClient.setQueryData<Account[]>(ACCOUNT_QUERY_KEYS.all, (old) =>
        sortByName((old ?? []).map((a) => (a.id === updatedAccount.id ? updatedAccount : a)))
      )
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.accounts.deleteAccount(id)
      return id
    },
    onSuccess: (deletedId) => {
      queryClient.setQueryData<Account[]>(ACCOUNT_QUERY_KEYS.all, (old) =>
        (old ?? []).filter((a) => a.id !== deletedId)
      )
    },
  })

  const setInitialBalanceMutation = useMutation({
    mutationFn: async ({
      id,
      balanceDate,
      balanceAmount,
    }: {
      id: string
      balanceDate: string
      balanceAmount: number
    }) => {
      return api.accounts.setInitialBalance(id, balanceDate, balanceAmount)
    },
    onSuccess: (updatedAccount) => {
      queryClient.setQueryData<Account[]>(ACCOUNT_QUERY_KEYS.all, (old) =>
        sortByName((old ?? []).map((a) => (a.id === updatedAccount.id ? updatedAccount : a)))
      )
    },
  })

  const deleteInitialBalanceMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.accounts.deleteInitialBalance(id)
      return id
    },
    onSuccess: (accountId) => {
      queryClient.setQueryData<Account[]>(ACCOUNT_QUERY_KEYS.all, (old) =>
        (old ?? []).map((a) => (a.id === accountId ? { ...a, initial_balance: undefined } : a))
      )
    },
  })

  const addAccount = useCallback(
    async (name: string, currency: string): Promise<Account | null> => {
      try {
        return await addMutation.mutateAsync({ name, currency })
      } catch {
        return null
      }
    },
    [addMutation]
  )

  const updateAccount = useCallback(
    async (id: string, name: string, currency: string): Promise<Account | null> => {
      try {
        return await updateMutation.mutateAsync({ id, name, currency })
      } catch {
        return null
      }
    },
    [updateMutation]
  )

  const deleteAccount = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await deleteMutation.mutateAsync(id)
        return true
      } catch {
        return false
      }
    },
    [deleteMutation]
  )

  const setInitialBalance = useCallback(
    async (id: string, balanceDate: string, balanceAmount: number): Promise<Account | null> => {
      try {
        return await setInitialBalanceMutation.mutateAsync({ id, balanceDate, balanceAmount })
      } catch {
        return null
      }
    },
    [setInitialBalanceMutation]
  )

  const deleteInitialBalance = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await deleteInitialBalanceMutation.mutateAsync(id)
        return true
      } catch {
        return false
      }
    },
    [deleteInitialBalanceMutation]
  )

  const exportAccounts = useCallback(async (): Promise<boolean> => {
    try {
      await api.accounts.exportAccounts()
      return true
    } catch {
      return false
    }
  }, [api.accounts])

  const uploadAccounts = useCallback(
    async (file: File) => {
      try {
        const result = await api.accounts.uploadAccounts(file)
        await queryClient.invalidateQueries({ queryKey: ACCOUNT_QUERY_KEYS.all })
        return result
      } catch {
        return null
      }
    },
    [api.accounts, queryClient]
  )

  const loading =
    accountsQuery.isLoading ||
    addMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    setInitialBalanceMutation.isPending ||
    deleteInitialBalanceMutation.isPending

  const error =
    accountsQuery.error || addMutation.error || updateMutation.error || deleteMutation.error
      ? getErrorMessage(accountsQuery.error || addMutation.error || updateMutation.error || deleteMutation.error)
      : null

  return {
    accounts: accountsQuery.data ?? [],
    loading,
    error,
    fetchAccounts: () => queryClient.invalidateQueries({ queryKey: ACCOUNT_QUERY_KEYS.all }),
    addAccount,
    updateAccount,
    deleteAccount,
    setInitialBalance,
    deleteInitialBalance,
    exportAccounts,
    uploadAccounts,
  }
}
