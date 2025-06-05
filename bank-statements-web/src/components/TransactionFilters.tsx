import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { CategorizationStatus, Category, Source } from '../types/Transaction'

interface TransactionFiltersProps {
  categories: Category[]
  sources: Source[]
  selectedCategoryIds?: string[]
  selectedStatus?: CategorizationStatus
  selectedSourceId?: string
  minAmount?: number
  maxAmount?: number
  descriptionSearch?: string
  onCategoryChange: (categoryIds: string[]) => void
  onStatusChange: (status?: CategorizationStatus) => void
  onSourceChange: (sourceId?: string) => void
  onAmountRangeChange: (minAmount?: number, maxAmount?: number) => void
  onDescriptionSearchChange: (search?: string) => void
  onClearFilters: () => void
}

export const TransactionFilters = ({
  categories,
  sources,
  selectedCategoryIds = [],
  selectedStatus,
  selectedSourceId,
  minAmount,
  maxAmount,
  descriptionSearch,
  onCategoryChange,
  onStatusChange,
  onSourceChange,
  onAmountRangeChange,
  onDescriptionSearchChange,
  onClearFilters,
}: TransactionFiltersProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

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
    selectedStatus ||
    minAmount !== undefined ||
    maxAmount !== undefined ||
    descriptionSearch ||
    selectedSourceId

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCategoryAdd = useCallback(
    (categoryId: string) => {
      if (!selectedCategoryIds.includes(categoryId)) {
        onCategoryChange([...selectedCategoryIds, categoryId])
      }
      setCategoryInput('')
      setShowSuggestions(false)
      inputRef.current?.focus()
    },
    [selectedCategoryIds, onCategoryChange]
  )

  const handleCategoryRemove = useCallback(
    (categoryId: string) => {
      onCategoryChange(selectedCategoryIds.filter((id) => id !== categoryId))
    },
    [selectedCategoryIds, onCategoryChange]
  )

  const handleInputChange = useCallback(
    (value: string) => {
      setCategoryInput(value)
      setShowSuggestions(value.length > 0 && availableCategories.length > 0)
    },
    [availableCategories.length]
  )

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

  const handleAmountChange = useCallback(
    (field: 'min' | 'max', value: string) => {
      const numValue = value === '' ? undefined : parseFloat(value)
      if (field === 'min') {
        onAmountRangeChange(numValue, maxAmount)
      } else {
        onAmountRangeChange(minAmount, numValue)
      }
    },
    [minAmount, maxAmount, onAmountRangeChange]
  )

  return (
    <div className="transaction-filters-advanced">
      <div className="filter-header">
        <h3>Filters</h3>
        {hasActiveFilters && (
          <button onClick={onClearFilters} className="clear-all-button">
            Clear All
          </button>
        )}
      </div>

      <div className="filters-grid">
        {/* Description Search */}
        <div className="filter-section">
          <label htmlFor="description-search" className="filter-label">
            Search Description
          </label>
          <input
            id="description-search"
            type="text"
            value={descriptionSearch || ''}
            onChange={(e) => onDescriptionSearchChange(e.target.value || undefined)}
            placeholder="Search transactions..."
            className="search-input"
          />
        </div>

        {/* Amount Range */}
        <div className="filter-section">
          <label className="filter-label">Amount Range</label>
          <div className="amount-range">
            <input
              type="number"
              value={minAmount ?? ''}
              onChange={(e) => handleAmountChange('min', e.target.value)}
              placeholder="Min"
              className="amount-input"
              step="0.01"
            />
            <span className="amount-separator">to</span>
            <input
              type="number"
              value={maxAmount ?? ''}
              onChange={(e) => handleAmountChange('max', e.target.value)}
              placeholder="Max"
              className="amount-input"
              step="0.01"
            />
          </div>
        </div>

        {/* Status Filter */}
        <div className="filter-section">
          <label htmlFor="status-filter" className="filter-label">
            Status
          </label>
          <select
            id="status-filter"
            value={selectedStatus || ''}
            onChange={(e) => onStatusChange((e.target.value as CategorizationStatus) || undefined)}
            className="filter-select"
          >
            <option value="">All Statuses</option>
            <option value="UNCATEGORIZED">Uncategorized</option>
            <option value="CATEGORIZED">Categorized</option>
            <option value="FAILURE">Failed</option>
          </select>
        </div>

        {/* Source Filter */}
        <div className="filter-section">
          <label htmlFor="source-filter" className="filter-label">
            Source
          </label>
          <select
            id="source-filter"
            value={selectedSourceId || ''}
            onChange={(e) => onSourceChange(e.target.value || undefined)}
            className="filter-select"
          >
            <option value="">All Sources</option>
            {sources.map((source) => (
              <option key={source.id} value={source.id}>
                {source.name}
              </option>
            ))}
          </select>
        </div>

        {/* Simple Categories Tag Input */}
        <div className="filter-section">
          <label className="filter-label">Categories</label>

          <div className="category-tag-input" ref={containerRef}>
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
                onFocus={() => setShowSuggestions(categoryInput.length > 0 && availableCategories.length > 0)}
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
      </div>
    </div>
  )
}
