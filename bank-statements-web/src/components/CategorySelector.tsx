import { useState, useMemo, useRef, useEffect } from 'react'
import { Category } from '../types/Transaction'
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
}: CategorySelectorProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Get selected category objects
  const selectedCategory = useMemo(() => {
    return categories.find((cat) => cat.id === selectedCategoryId)
  }, [categories, selectedCategoryId])

  const selectedCategories = useMemo(() => {
    return categories.filter((cat) => selectedCategoryIds.includes(cat.id))
  }, [categories, selectedCategoryIds])

  // Filter categories based on input and availability
  const filteredCategories = useMemo(() => {
    let availableCategories = categories

    if (multiple) {
      // For multiple selection, exclude already selected categories
      availableCategories = categories.filter((category) => !selectedCategoryIds.includes(category.id))
    } else {
      // For single selection, only show leaf categories (no children)
      availableCategories = categories.filter((category) => {
        const hasChildren = categories.some((cat) => cat.parent_id === category.id)
        return !hasChildren
      })
    }

    if (!categoryInput) return availableCategories
    return availableCategories.filter((category) => category.name.toLowerCase().includes(categoryInput.toLowerCase()))
  }, [categories, categoryInput, multiple, selectedCategoryIds])

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
    setShowSuggestions(true)
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

  // Display text for the input
  const inputDisplayValue = multiple
    ? categoryInput
    : categoryInput || (selectedCategory && !showSuggestions ? getCategoryHierarchy(selectedCategory) : '')

  // Placeholder text
  const placeholderText = multiple && selectedCategories.length > 0 ? 'Add more categories...' : placeholder

  return (
    <div className={`category-selector ${multiple ? 'multiple' : 'single'}`} ref={containerRef}>
      <div className="category-selector-input-container">
        {/* Selected categories tags (multiple mode only) */}
        {multiple &&
          selectedCategories.map((category) => (
            <span key={category.id} className="category-tag">
              {category.name}
              <button
                onClick={() => handleCategoryRemove(category.id)}
                className="category-tag-remove"
                type="button"
                title={`Remove ${category.name}`}
              >
                ×
              </button>
            </span>
          ))}

        <input
          ref={inputRef}
          type="text"
          value={inputDisplayValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={handleInputFocus}
          onKeyDown={handleInputKeyDown}
          placeholder={placeholderText}
          className="category-input"
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
          {filteredCategories.length > 0 ? (
            filteredCategories.map((category) => (
              <button
                key={category.id}
                onClick={() => handleCategorySelect(category)}
                className="category-suggestion"
                type="button"
              >
                {multiple && category.parent_id && '  └ '}
                {multiple ? category.name : getCategoryHierarchy(category)}
              </button>
            ))
          ) : (
            <div className="no-suggestions">No categories found</div>
          )}
        </div>
      )}
    </div>
  )
}
