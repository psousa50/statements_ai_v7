import { useState, useMemo, useRef, useEffect } from 'react'
import { Category } from '../types/Transaction'
import { getCategoryColorById } from '../utils/categoryColors'
import './CategorySelector.css'

interface CategorySelectorProps {
  categories: Category[]
  selectedCategoryId?: string
  selectedCategoryIds?: string[]
  onCategoryChange: (categoryId?: string) => void
  onCategoryIdsChange?: (categoryIds: string[]) => void
  placeholder?: string
  allowClear?: boolean
  multiple?: boolean
  variant?: 'default' | 'filter' | 'form'
  autoFocus?: boolean
  allowCreate?: boolean
  onCategoryCreate?: (name: string, parentId?: string) => Promise<Category | null>
  allowParentCategories?: boolean
}

export const CategorySelector = ({
  categories,
  selectedCategoryId,
  selectedCategoryIds = [],
  onCategoryChange,
  onCategoryIdsChange,
  placeholder = 'Select a category',
  allowClear = true,
  multiple = false,
  variant = 'default',
  autoFocus = false,
  allowCreate = false,
  onCategoryCreate,
  allowParentCategories = false,
}: CategorySelectorProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [creatingCategory, setCreatingCategory] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Get selected category objects
  const selectedCategory = useMemo(() => {
    return categories.find((cat) => cat.id === selectedCategoryId)
  }, [categories, selectedCategoryId])

  const selectedCategories = useMemo(() => {
    return categories.filter((cat) => selectedCategoryIds.includes(cat.id))
  }, [categories, selectedCategoryIds])

  // Parse create pattern (e.g., "car > parking")
  const createPattern = useMemo(() => {
    if (!allowCreate || !categoryInput.includes('>')) {
      return null
    }

    const parts = categoryInput.split('>').map((part) => part.trim())
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      return null
    }

    const [parentName, childName] = parts
    const parentCategory = categories.find(
      (cat) => cat.name.toLowerCase() === parentName.toLowerCase() && !cat.parent_id
    )

    if (!parentCategory) {
      return null
    }

    const childExists = categories.some(
      (cat) => cat.parent_id === parentCategory.id && cat.name.toLowerCase() === childName.toLowerCase()
    )

    if (childExists) {
      return null
    }

    return {
      parentCategory,
      childName,
    }
  }, [allowCreate, categoryInput, categories])

  // Filter categories based on input and availability
  const filteredCategories = useMemo(() => {
    let availableCategories = categories

    if (multiple) {
      availableCategories = categories.filter((category) => !selectedCategoryIds.includes(category.id))
    } else if (allowParentCategories) {
      availableCategories = categories.filter((category) => !category.parent_id)
    } else {
      availableCategories = categories.filter((category) => {
        const hasChildren = categories.some((cat) => cat.parent_id === category.id)
        return !hasChildren
      })
    }

    const filtered = !categoryInput
      ? availableCategories
      : availableCategories.filter((category) => {
          const searchLower = categoryInput.toLowerCase()
          const categoryNameMatch = category.name.toLowerCase().includes(searchLower)
          const parentCategory = categories.find((cat) => cat.id === category.parent_id)
          const parentNameMatch = parentCategory ? parentCategory.name.toLowerCase().includes(searchLower) : false
          return categoryNameMatch || parentNameMatch
        })

    return filtered.sort((a, b) => a.name.localeCompare(b.name))
  }, [categories, categoryInput, multiple, selectedCategoryIds, allowParentCategories])

  // Get category hierarchy display name
  const getCategoryHierarchy = (category: Category): string => {
    const parentCategory = categories.find((cat) => cat.id === category.parent_id)
    return parentCategory ? `${parentCategory.name} > ${category.name}` : category.name
  }

  // Handle input changes
  const handleInputChange = (value: string) => {
    setCategoryInput(value)
    setShowSuggestions(true)
  }

  // Handle category selection
  const handleCategorySelect = (category: Category) => {
    if (multiple && onCategoryIdsChange) {
      const newIds = [...selectedCategoryIds, category.id]
      onCategoryIdsChange(newIds)
      setCategoryInput('')
      setShowSuggestions(false)
      inputRef.current?.focus()
    } else {
      onCategoryChange(category.id)
      setCategoryInput('')
      setShowSuggestions(false)
      inputRef.current?.blur()
    }
  }

  // Handle category creation
  const handleCreateCategory = async () => {
    if (!createPattern || !onCategoryCreate) return

    setCreatingCategory(true)
    try {
      const newCategory = await onCategoryCreate(createPattern.childName, createPattern.parentCategory.id)
      if (newCategory) {
        handleCategorySelect(newCategory)
      }
    } catch (error) {
      console.error('Failed to create category:', error)
    } finally {
      setCreatingCategory(false)
    }
  }

  // Handle category removal (multiple mode only)
  const handleCategoryRemove = (categoryId: string) => {
    if (multiple && onCategoryIdsChange) {
      const newIds = selectedCategoryIds.filter((id) => id !== categoryId)
      onCategoryIdsChange(newIds)
    }
  }

  // Handle clear selection
  const handleClear = () => {
    if (multiple && onCategoryIdsChange) {
      onCategoryIdsChange([])
    } else {
      onCategoryChange(undefined)
    }
    setCategoryInput('')
    setShowSuggestions(false)
  }

  // Handle input focus
  const handleInputFocus = () => {
    // Clear input when focusing to allow typing search
    if (!multiple && selectedCategory) {
      setCategoryInput('')
    }
  }

  // Handle input key down for multiple mode
  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (multiple) {
      if (e.key === 'Enter' && filteredCategories.length > 0) {
        e.preventDefault()
        handleCategorySelect(filteredCategories[0])
      } else if (e.key === 'Escape') {
        setShowSuggestions(false)
        setCategoryInput('')
      } else if (e.key === 'Backspace' && categoryInput === '' && selectedCategories.length > 0) {
        // Remove last selected category when backspacing on empty input
        handleCategoryRemove(selectedCategories[selectedCategories.length - 1].id)
      }
    }
  }

  // Handle clicks outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
        setCategoryInput('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Force color fix for dark mode
  useEffect(() => {
    if (inputRef.current) {
      const textPrimary = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim()
      if (textPrimary) {
        inputRef.current.style.color = textPrimary
        inputRef.current.style.setProperty('color', textPrimary, 'important')
      } else {
        // Fallback for dark mode detection
        const isDark =
          document.documentElement.getAttribute('data-theme') === 'dark' ||
          document.body.classList.contains('rs-theme-dark')
        if (isDark) {
          inputRef.current.style.setProperty('color', 'rgba(255, 255, 255, 0.87)', 'important')
        }
      }
    }
  }, [showSuggestions, variant])

  // Handle autofocus
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }, [autoFocus])

  // Display text for the input
  const inputDisplayValue = multiple
    ? categoryInput
    : categoryInput || (selectedCategory && !showSuggestions ? getCategoryHierarchy(selectedCategory) : '')

  // Placeholder text
  const placeholderText = multiple && selectedCategories.length > 0 ? 'Add more categories...' : placeholder

  const showSingleCategoryChip = !multiple && selectedCategory && !showSuggestions

  return (
    <div className={`category-selector ${multiple ? 'multiple' : 'single'} variant-${variant}`} ref={containerRef}>
      <div className="category-selector-input-container">
        {/* Selected category chip (single mode) */}
        {showSingleCategoryChip && (
          <span
            className="category-tag category-tag-gradient"
            style={{ background: getCategoryColorById(selectedCategory.id).gradient }}
            onClick={() => inputRef.current?.focus()}
          >
            {getCategoryHierarchy(selectedCategory)}
          </span>
        )}

        {/* Selected categories tags (multiple mode) */}
        {multiple &&
          selectedCategories.map((category) => {
            const colorConfig = getCategoryColorById(category.id)
            return (
              <span
                key={category.id}
                className="category-tag category-tag-gradient"
                style={{ background: colorConfig.gradient }}
              >
                {getCategoryHierarchy(category)}
                <button
                  onClick={() => handleCategoryRemove(category.id)}
                  className="category-tag-remove"
                  type="button"
                  title={`Remove ${getCategoryHierarchy(category)}`}
                >
                  ×
                </button>
              </span>
            )
          })}

        <input
          ref={inputRef}
          type="text"
          value={showSingleCategoryChip ? categoryInput : inputDisplayValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={handleInputFocus}
          onKeyDown={handleInputKeyDown}
          placeholder={showSingleCategoryChip ? '' : placeholderText}
          className={`category-input ${showSingleCategoryChip ? 'category-input-hidden' : ''}`}
          autoFocus={autoFocus}
          style={{
            color: 'var(--text-primary)',
            backgroundColor: 'transparent',
          }}
        />

        {/* Clear button */}
        {allowClear && ((multiple && selectedCategories.length > 0) || (!multiple && selectedCategory)) && (
          <button type="button" onClick={handleClear} className="category-clear-button" title="Clear selection">
            ×
          </button>
        )}
      </div>

      {showSuggestions && (
        <div className="category-suggestions">
          {createPattern && (
            <button
              onClick={handleCreateCategory}
              className="category-suggestion category-create"
              type="button"
              disabled={creatingCategory}
            >
              {creatingCategory ? (
                <>Creating...</>
              ) : (
                <>
                  ✨ Create "{createPattern.parentCategory.name} &gt; {createPattern.childName}"
                </>
              )}
            </button>
          )}
          {filteredCategories.length > 0 ? (
            filteredCategories.map((category) => (
              <button
                key={category.id}
                onClick={() => handleCategorySelect(category)}
                className="category-suggestion"
                type="button"
              >
                {getCategoryHierarchy(category)}
              </button>
            ))
          ) : !createPattern ? (
            <div className="no-suggestions">No categories found</div>
          ) : null}
        </div>
      )}
    </div>
  )
}
