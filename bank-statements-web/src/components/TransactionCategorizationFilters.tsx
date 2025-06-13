import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Category } from '../types/Transaction'
import { CategorizationSource } from '../types/TransactionCategorization'

interface TransactionCategorizationFiltersProps {
  categories: Category[]
  selectedCategoryIds?: string[]
  selectedSource?: CategorizationSource
  descriptionSearch?: string
  onCategoryChange: (categoryIds: string[]) => void
  onSourceChange: (source?: CategorizationSource) => void
  onDescriptionSearchChange: (search?: string) => void
  onClearFilters: () => void
}

export const TransactionCategorizationFilters = ({
  categories,
  selectedCategoryIds = [],
  selectedSource,
  descriptionSearch,
  onCategoryChange,
  onSourceChange,
  onDescriptionSearchChange,
  onClearFilters,
}: TransactionCategorizationFiltersProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const categoryContainerRef = useRef<HTMLDivElement>(null)
  const isAddingCategoryRef = useRef(false)

  // Filter categories based on input and exclude already selected ones
  const availableCategories = useMemo(() => {
    return categories.filter(
      (category) =>
        !selectedCategoryIds.includes(category.id) && category.name.toLowerCase().includes(categoryInput.toLowerCase())
    )
  }, [categories, selectedCategoryIds, categoryInput])

  // Get selected category objects
  const selectedCategories = useMemo(() => {
    return categories.filter((cat) => selectedCategoryIds.includes(cat.id))
  }, [categories, selectedCategoryIds])

  const hasActiveFilters =
    selectedCategoryIds.length > 0 ||
    selectedSource ||
    descriptionSearch

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      const isCategoryClick = target && categoryContainerRef.current?.contains(target)

      if (!isCategoryClick) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCategoryAdd = useCallback(
    (categoryId: string) => {
      isAddingCategoryRef.current = true
      if (!selectedCategoryIds.includes(categoryId)) {
        onCategoryChange([...selectedCategoryIds, categoryId])
      }
      setCategoryInput('')
      setShowSuggestions(false)

      // Reset the flag after a short delay and refocus
      setTimeout(() => {
        isAddingCategoryRef.current = false
        inputRef.current?.focus()
      }, 0)
    },
    [selectedCategoryIds, onCategoryChange]
  )

  const handleCategoryRemove = useCallback(
    (categoryId: string) => {
      onCategoryChange(selectedCategoryIds.filter((id) => id !== categoryId))
    },
    [selectedCategoryIds, onCategoryChange]
  )

  const handleInputChange = useCallback((value: string) => {
    setCategoryInput(value)
    setShowSuggestions(value.length > 0)
  }, [])

  const handleInputKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && availableCategories.length > 0) {
        e.preventDefault()
        handleCategoryAdd(availableCategories[0].id)
      } else if (e.key === 'Escape') {
        setShowSuggestions(false)
        setCategoryInput('')
      } else if (e.key === 'Backspace' && categoryInput === '' && selectedCategories.length > 0) {
        // Remove last selected category when backspacing on empty input
        handleCategoryRemove(selectedCategories[selectedCategories.length - 1].id)
      }
    },
    [availableCategories, categoryInput, selectedCategories, handleCategoryAdd, handleCategoryRemove]
  )

  return (
    <div className="transaction-filters-advanced">
      <div className="filters-grid-horizontal">
        {/* Search Description */}
        <div className="filter-section">
          <input
            id="description-search"
            type="text"
            value={descriptionSearch || ''}
            onChange={(e) => onDescriptionSearchChange(e.target.value || undefined)}
            placeholder="Search descriptions..."
            className="search-input"
          />
        </div>

        {/* Source Filter */}
        <div className="filter-section">
          <select
            id="source-filter"
            value={selectedSource || ''}
            onChange={(e) => onSourceChange((e.target.value as CategorizationSource) || undefined)}
            className="filter-select"
          >
            <option value="">All Sources</option>
            <option value={CategorizationSource.MANUAL}>👤 Manual</option>
            <option value={CategorizationSource.AI}>🤖 AI</option>
          </select>
        </div>

        {/* Categories */}
        <div className="filter-section filter-section-categories">
          <div className="category-tag-input" ref={categoryContainerRef}>
            <div className="tag-input-container">
              {/* Selected Categories Tags */}
              {selectedCategories.map((category) => (
                <span key={category.id} className="category-tag">
                  {category.name}
                  <button
                    onClick={() => handleCategoryRemove(category.id)}
                    className="category-tag-remove"
                    type="button"
                  >
                    ×
                  </button>
                </span>
              ))}

              {/* Input Field */}
              <input
                ref={inputRef}
                type="text"
                value={categoryInput}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={handleInputKeyDown}
                onFocus={() => {
                  // Don't show suggestions if we're in the middle of adding a category
                  if (!isAddingCategoryRef.current && categoryInput.length > 0) {
                    setShowSuggestions(true)
                  }
                }}
                placeholder={selectedCategories.length === 0 ? 'Type to add categories...' : 'Add more...'}
                className="category-input"
              />
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && availableCategories.length > 0 && (
              <div className="category-suggestions">
                {availableCategories.slice(0, 8).map((category) => (
                  <button
                    key={category.id}
                    onClick={() => handleCategoryAdd(category.id)}
                    className="category-suggestion"
                    type="button"
                  >
                    {category.parent_id && '  └ '}
                    {category.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Clear All Button */}
        {hasActiveFilters && (
          <div className="filter-section">
            <button onClick={onClearFilters} className="clear-all-button">
              Clear All
            </button>
          </div>
        )}
      </div>
    </div>
  )
}