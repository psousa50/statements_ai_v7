import { useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Category } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'

const sortByName = (categories: Category[]) => [...categories].sort((a, b) => a.name.localeCompare(b.name))

export const CATEGORY_QUERY_KEYS = {
  all: ['categories'] as const,
  root: ['categories', 'root'] as const,
  subcategories: (parentId: string) => ['categories', 'subcategories', parentId] as const,
}

export const useCategories = () => {
  const api = useApi()
  const queryClient = useQueryClient()

  const categoriesQuery = useQuery({
    queryKey: CATEGORY_QUERY_KEYS.all,
    queryFn: async () => {
      const response = await api.categories.getAll()
      return sortByName(response.categories)
    },
  })

  const rootCategoriesQuery = useQuery({
    queryKey: CATEGORY_QUERY_KEYS.root,
    queryFn: async () => {
      const response = await api.categories.getRootCategories()
      return sortByName(response.categories)
    },
  })

  const fetchSubcategories = useCallback(
    async (parentId: string) => {
      const cached = queryClient.getQueryData<Category[]>(CATEGORY_QUERY_KEYS.subcategories(parentId))
      if (cached) return cached

      const response = await api.categories.getSubcategories(parentId)
      const sorted = sortByName(response.categories)
      queryClient.setQueryData(CATEGORY_QUERY_KEYS.subcategories(parentId), sorted)
      return sorted
    },
    [api.categories, queryClient]
  )

  const addMutation = useMutation({
    mutationFn: async ({
      name,
      parentId,
      color,
      excludeFromSpending,
      isIrregular,
    }: {
      name: string
      parentId?: string
      color?: string
      excludeFromSpending?: boolean
      isIrregular?: boolean
    }) => {
      return api.categories.create({
        name,
        parent_id: parentId,
        color,
        exclude_from_spending: excludeFromSpending,
        is_irregular: isIrregular,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.root })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      name,
      parentId,
      color,
      excludeFromSpending,
      isIrregular,
    }: {
      id: string
      name: string
      parentId?: string
      color?: string
      excludeFromSpending?: boolean
      isIrregular?: boolean
    }) => {
      return api.categories.update(id, {
        name,
        parent_id: parentId,
        color,
        exclude_from_spending: excludeFromSpending,
        is_irregular: isIrregular,
      })
    },
    onMutate: async ({ id, name, parentId, color, excludeFromSpending, isIrregular }) => {
      await queryClient.cancelQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
      await queryClient.cancelQueries({ queryKey: CATEGORY_QUERY_KEYS.root })
      const previousAll = queryClient.getQueryData<Category[]>(CATEGORY_QUERY_KEYS.all)
      const previousRoot = queryClient.getQueryData<Category[]>(CATEGORY_QUERY_KEYS.root)
      const applyPatch = (list?: Category[]) =>
        list?.map((c) =>
          c.id === id
            ? {
                ...c,
                name,
                parent_id: parentId,
                color,
                exclude_from_spending: excludeFromSpending ?? c.exclude_from_spending,
                is_irregular: isIrregular ?? c.is_irregular,
              }
            : c
        )
      queryClient.setQueryData<Category[]>(CATEGORY_QUERY_KEYS.all, (old) => applyPatch(old) ?? old)
      queryClient.setQueryData<Category[]>(CATEGORY_QUERY_KEYS.root, (old) => applyPatch(old) ?? old)
      return { previousAll, previousRoot }
    },
    onError: (_err, _vars, context) => {
      if (context?.previousAll) queryClient.setQueryData(CATEGORY_QUERY_KEYS.all, context.previousAll)
      if (context?.previousRoot) queryClient.setQueryData(CATEGORY_QUERY_KEYS.root, context.previousRoot)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.root })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.categories.delete(id)
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.root })
    },
  })

  const exportMutation = useMutation({
    mutationFn: async () => {
      await api.categories.exportCategories()
      return true
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return api.categories.uploadCategories(file)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.root })
    },
  })

  const addCategory = useCallback(
    async (name: string, parentId?: string, color?: string, excludeFromSpending?: boolean, isIrregular?: boolean) => {
      try {
        return await addMutation.mutateAsync({ name, parentId, color, excludeFromSpending, isIrregular })
      } catch {
        return null
      }
    },
    [addMutation]
  )

  const updateCategory = useCallback(
    async (
      id: string,
      name: string,
      parentId?: string,
      color?: string,
      excludeFromSpending?: boolean,
      isIrregular?: boolean
    ) => {
      try {
        return await updateMutation.mutateAsync({ id, name, parentId, color, excludeFromSpending, isIrregular })
      } catch {
        return null
      }
    },
    [updateMutation]
  )

  const deleteCategory = useCallback(
    async (id: string) => {
      try {
        await deleteMutation.mutateAsync(id)
        return true
      } catch {
        return false
      }
    },
    [deleteMutation]
  )

  const exportCategories = useCallback(async () => {
    try {
      await exportMutation.mutateAsync()
      return true
    } catch {
      return false
    }
  }, [exportMutation])

  const uploadCategories = useCallback(
    async (file: File) => {
      try {
        return await uploadMutation.mutateAsync(file)
      } catch {
        return null
      }
    },
    [uploadMutation]
  )

  const loading = categoriesQuery.isLoading || rootCategoriesQuery.isLoading
  const mutating =
    addMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    exportMutation.isPending ||
    uploadMutation.isPending

  const error = categoriesQuery.error?.message || rootCategoriesQuery.error?.message || null

  return {
    categories: categoriesQuery.data ?? [],
    rootCategories: rootCategoriesQuery.data ?? [],
    loading,
    mutating,
    error,
    fetchCategories: () => queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.all }),
    fetchRootCategories: () => queryClient.invalidateQueries({ queryKey: CATEGORY_QUERY_KEYS.root }),
    fetchSubcategories,
    addCategory,
    updateCategory,
    deleteCategory,
    exportCategories,
    uploadCategories,
  }
}
