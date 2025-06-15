import { useState, useMemo, useRef, useEffect } from 'react'
import { Category } from '../types/Transaction'

interface CategorySelectorProps {
  categories: Category[]
  selectedCategoryId?: string
  onCategoryChange: (categoryId?: string) => void
  placeholder?: string
  allowClear?: boolean
}

export const CategorySelector = ({
  categories,
  selectedCategoryId,
  onCategoryChange,
  placeholder = "Select a category",
  allowClear = true,
}: CategorySelectorProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Get selected category object
  const selectedCategory = useMemo(() => {
    return categories.find(cat => cat.id === selectedCategoryId)
  }, [categories, selectedCategoryId])

  // Filter categories based on input and only show leaf categories (no children)
  const filteredCategories = useMemo(() => {
    // Only show categories that don't have children (leaf categories)
    const leafCategories = categories.filter(category => {
      const hasChildren = categories.some(cat => cat.parent_id === category.id)
      return !hasChildren
    })
    
    if (!categoryInput) return leafCategories
    return leafCategories.filter(category =>
      category.name.toLowerCase().includes(categoryInput.toLowerCase())
    )
  }, [categories, categoryInput])

  // Get category hierarchy display name
  const getCategoryHierarchy = (category: Category): string => {
    const parentCategory = categories.find(cat => cat.id === category.parent_id)
    return parentCategory ? `${parentCategory.name} > ${category.name}` : category.name
  }

  // Handle input changes
  const handleInputChange = (value: string) => {
    setCategoryInput(value)
    setShowSuggestions(true)
  }

  // Handle category selection
  const handleCategorySelect = (category: Category) => {
    onCategoryChange(category.id)
    setCategoryInput('')
    setShowSuggestions(false)
    inputRef.current?.blur()
  }

  // Handle clear selection
  const handleClear = () => {
    onCategoryChange(undefined)
    setCategoryInput('')
    setShowSuggestions(false)
  }

  // Handle input focus
  const handleInputFocus = () => {
    setShowSuggestions(true)
    // Clear input when focusing to allow typing search
    if (selectedCategory) {
      setCategoryInput('')
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

  // Display text for the input (either search term or selected category)
  const inputDisplayValue = categoryInput || (selectedCategory && !showSuggestions 
    ? getCategoryHierarchy(selectedCategory)
    : '')

  return (
    <div className="category-selector" ref={containerRef}>
      <div className="category-selector-input-container">
        <input
          ref={inputRef}
          type="text"
          value={inputDisplayValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="category-input"
        />
        {selectedCategory && allowClear && (
          <button
            type="button"
            onClick={handleClear}
            className="category-clear-button"
            title="Clear selection"
          >
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
                {getCategoryHierarchy(category)}
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