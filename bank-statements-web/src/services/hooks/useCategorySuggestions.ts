import { useState, useCallback } from 'react'
import { useApi } from '../../api/ApiContext'
import { CategorySuggestion, CategorySelectionItem } from '../../api/CategoryClient'

export const useCategorySuggestions = () => {
  const api = useApi()
  const [suggestions, setSuggestions] = useState<CategorySuggestion[]>([])
  const [selectedItems, setSelectedItems] = useState<Map<string, Set<string>>>(new Map())
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalDescriptionsAnalysed, setTotalDescriptionsAnalysed] = useState(0)

  const generateSuggestions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.categories.generateSuggestions()
      setSuggestions(response.suggestions)
      setTotalDescriptionsAnalysed(response.total_descriptions_analysed)

      const initialSelection = new Map<string, Set<string>>()
      response.suggestions.forEach((suggestion) => {
        const newSubcategories = suggestion.subcategories.filter((sub) => sub.is_new).map((sub) => sub.name)
        if (suggestion.parent_is_new || newSubcategories.length > 0) {
          initialSelection.set(suggestion.parent_name, new Set(newSubcategories))
        }
      })
      setSelectedItems(initialSelection)
    } catch (err) {
      console.error('Error generating category suggestions:', err)
      setError('Failed to generate category suggestions. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [api.categories])

  const toggleParent = useCallback((parentName: string, suggestion: CategorySuggestion) => {
    setSelectedItems((prev) => {
      const newMap = new Map(prev)
      if (newMap.has(parentName)) {
        newMap.delete(parentName)
      } else {
        const newSubcategories = suggestion.subcategories.filter((sub) => sub.is_new).map((sub) => sub.name)
        newMap.set(parentName, new Set(newSubcategories))
      }
      return newMap
    })
  }, [])

  const toggleSubcategory = useCallback(
    (parentName: string, subcategoryName: string) => {
      setSelectedItems((prev) => {
        const newMap = new Map(prev)
        const currentSubs = newMap.get(parentName) || new Set()
        const newSubs = new Set(currentSubs)

        if (newSubs.has(subcategoryName)) {
          newSubs.delete(subcategoryName)
        } else {
          newSubs.add(subcategoryName)
        }

        if (newSubs.size === 0) {
          const suggestion = suggestions.find((s) => s.parent_name === parentName)
          if (suggestion && !suggestion.parent_is_new) {
            newMap.delete(parentName)
          } else {
            newMap.set(parentName, newSubs)
          }
        } else {
          newMap.set(parentName, newSubs)
        }

        return newMap
      })
    },
    [suggestions]
  )

  const createSelected = useCallback(async () => {
    setCreating(true)
    setError(null)
    try {
      const selections: CategorySelectionItem[] = []

      selectedItems.forEach((subcategoryNames, parentName) => {
        const suggestion = suggestions.find((s) => s.parent_name === parentName)
        if (suggestion) {
          selections.push({
            parent_name: parentName,
            parent_id: suggestion.parent_id,
            subcategory_names: Array.from(subcategoryNames),
          })
        }
      })

      if (selections.length === 0) {
        return { categories_created: 0, categories: [] }
      }

      const response = await api.categories.createSelectedCategories({ selections })
      setSuggestions([])
      setSelectedItems(new Map())
      return response
    } catch (err) {
      console.error('Error creating selected categories:', err)
      setError('Failed to create categories. Please try again later.')
      return null
    } finally {
      setCreating(false)
    }
  }, [api.categories, selectedItems, suggestions])

  const reset = useCallback(() => {
    setSuggestions([])
    setSelectedItems(new Map())
    setError(null)
    setTotalDescriptionsAnalysed(0)
  }, [])

  const getSelectedCount = useCallback(() => {
    let parentCount = 0
    let subcategoryCount = 0

    selectedItems.forEach((subs, parentName) => {
      const suggestion = suggestions.find((s) => s.parent_name === parentName)
      if (suggestion?.parent_is_new) {
        parentCount++
      }
      subcategoryCount += subs.size
    })

    return { parentCount, subcategoryCount, total: parentCount + subcategoryCount }
  }, [selectedItems, suggestions])

  return {
    suggestions,
    selectedItems,
    loading,
    creating,
    error,
    totalDescriptionsAnalysed,
    generateSuggestions,
    toggleParent,
    toggleSubcategory,
    createSelected,
    reset,
    getSelectedCount,
  }
}
