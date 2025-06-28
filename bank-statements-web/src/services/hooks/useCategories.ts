import { useState, useEffect, useCallback } from 'react'
import { Category } from '../../types/Transaction'
import { useApi } from '../../api/ApiContext'

export const useCategories = () => {
  const api = useApi()
  const [categories, setCategories] = useState<Category[]>([])
  const [rootCategories, setRootCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCategories = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.categories.getAll()
      setCategories(response.categories.sort((a, b) => a.name.localeCompare(b.name)))
    } catch (err) {
      console.error('Error fetching categories:', err)
      setError('Failed to fetch categories. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.categories])

  const fetchRootCategories = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.categories.getRootCategories()
      setRootCategories(response.categories.sort((a, b) => a.name.localeCompare(b.name)))
    } catch (err) {
      console.error('Error fetching root categories:', err)
      setError('Failed to fetch root categories. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.categories])

  const fetchSubcategories = useCallback(
    async (parentId: string) => {
      setLoading(true)
      setError(null)
      try {
        const response = await api.categories.getSubcategories(parentId)
        return response.categories.sort((a, b) => a.name.localeCompare(b.name))
      } catch (err) {
        console.error('Error fetching subcategories:', err)
        setError('Failed to fetch subcategories. Please try again later.')
        return []
      } finally {
        setLoading(false)
      }
    },
    [api.categories]
  )

  const addCategory = useCallback(
    async (name: string, parentId?: string) => {
      setLoading(true)
      setError(null)
      try {
        const newCategory = await api.categories.create({
          name,
          parent_id: parentId,
        })
        setCategories((prev) => [...prev, newCategory].sort((a, b) => a.name.localeCompare(b.name)))
        if (!parentId) {
          setRootCategories((prev) => [...prev, newCategory].sort((a, b) => a.name.localeCompare(b.name)))
        }
        return newCategory
      } catch (err) {
        console.error('Error adding category:', err)
        setError('Failed to add category. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.categories]
  )

  const updateCategory = useCallback(
    async (id: string, name: string, parentId?: string) => {
      setLoading(true)
      setError(null)
      try {
        const updatedCategory = await api.categories.update(id, {
          name,
          parent_id: parentId,
        })
        setCategories((prev) =>
          prev
            .map((category) => (category.id === id ? updatedCategory : category))
            .sort((a, b) => a.name.localeCompare(b.name))
        )
        setRootCategories((prev) => {
          let updated
          // If the category was a root category and now has a parent, remove it from root categories
          if (parentId && !prev.find((c) => c.id === id)?.parent_id) {
            updated = prev.filter((category) => category.id !== id)
          }
          // If the category was not a root category and now has no parent, add it to root categories
          else if (!parentId && prev.find((c) => c.id === id)?.parent_id) {
            updated = [...prev, updatedCategory]
          }
          // Otherwise, just update it if it's in the root categories
          else {
            updated = prev.map((category) => (category.id === id ? updatedCategory : category))
          }
          return updated.sort((a, b) => a.name.localeCompare(b.name))
        })
        return updatedCategory
      } catch (err) {
        console.error('Error updating category:', err)
        setError('Failed to update category. Please try again later.')
        return null
      } finally {
        setLoading(false)
      }
    },
    [api.categories]
  )

  const deleteCategory = useCallback(
    async (id: string) => {
      setLoading(true)
      setError(null)
      try {
        await api.categories.delete(id)
        setCategories((prev) => prev.filter((category) => category.id !== id))
        setRootCategories((prev) => prev.filter((category) => category.id !== id))
        return true
      } catch (err) {
        console.error('Error deleting category:', err)
        setError('Failed to delete category. Please try again later.')
        return false
      } finally {
        setLoading(false)
      }
    },
    [api.categories]
  )

  useEffect(() => {
    fetchCategories()
    fetchRootCategories()
  }, [fetchCategories, fetchRootCategories])

  return {
    categories,
    rootCategories,
    loading,
    error,
    fetchCategories,
    fetchRootCategories,
    fetchSubcategories,
    addCategory,
    updateCategory,
    deleteCategory,
  }
}
