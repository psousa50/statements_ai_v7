import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useApi } from '../../api/ApiContext'
import { TRANSACTION_QUERY_KEYS } from './useTransactions'

export const TAG_QUERY_KEYS = {
  all: ['tags'] as const,
  list: () => ['tags', 'list'] as const,
}

export const useTags = () => {
  const api = useApi()
  const queryClient = useQueryClient()

  const tagsQuery = useQuery({
    queryKey: TAG_QUERY_KEYS.list(),
    queryFn: async () => {
      const response = await api.tags.getAll()
      return response.tags.sort((a, b) => a.name.localeCompare(b.name))
    },
  })

  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      return api.tags.create(name)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAG_QUERY_KEYS.all })
    },
  })

  const addToTransactionMutation = useMutation({
    mutationFn: async ({ transactionId, tagId }: { transactionId: string; tagId: string }) => {
      return api.tags.addToTransaction(transactionId, tagId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAG_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const removeFromTransactionMutation = useMutation({
    mutationFn: async ({ transactionId, tagId }: { transactionId: string; tagId: string }) => {
      return api.tags.removeFromTransaction(transactionId, tagId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAG_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: TRANSACTION_QUERY_KEYS.all })
    },
  })

  const createTag = useCallback(
    async (name: string) => {
      try {
        return await createMutation.mutateAsync(name)
      } catch {
        return null
      }
    },
    [createMutation]
  )

  const addTagToTransaction = useCallback(
    async (transactionId: string, tagId: string) => {
      try {
        return await addToTransactionMutation.mutateAsync({ transactionId, tagId })
      } catch {
        return null
      }
    },
    [addToTransactionMutation]
  )

  const removeTagFromTransaction = useCallback(
    async (transactionId: string, tagId: string) => {
      try {
        return await removeFromTransactionMutation.mutateAsync({ transactionId, tagId })
      } catch {
        return null
      }
    },
    [removeFromTransactionMutation]
  )

  return {
    tags: tagsQuery.data ?? [],
    loading: tagsQuery.isLoading,
    error: tagsQuery.error?.message || null,
    createTag,
    addTagToTransaction,
    removeTagFromTransaction,
    isCreating: createMutation.isPending,
  }
}
