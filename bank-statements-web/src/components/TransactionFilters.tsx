import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { DateRangePicker } from 'rsuite'
import { CategorizationStatus, Category, Source } from '../types/Transaction'
import 'rsuite/dist/rsuite.min.css'

interface TransactionFiltersProps {
  categories: Category[]
  sources: Source[]
  selectedCategoryIds?: string[]
  selectedStatus?: CategorizationStatus
  selectedSourceId?: string
  minAmount?: number
  maxAmount?: number
  descriptionSearch?: string
  startDate?: string
  endDate?: string
  onCategoryChange: (categoryIds: string[]) => void
  onStatusChange: (status?: CategorizationStatus) => void
  onSourceChange: (sourceId?: string) => void
  onAmountRangeChange: (minAmount?: number, maxAmount?: number) => void
  onDescriptionSearchChange: (search?: string) => void
  onDateRangeChange?: (startDate?: string, endDate?: string) => void
  onClearFilters: () => void
}

const formatDateForInput = (date: Date): string => {
  // Ensure we're working with a valid date and format it as YYYY-MM-DD
  const validDate = new Date(date)
  if (isNaN(validDate.getTime())) {
    throw new Error('Invalid date provided to formatDateForInput')
  }

  const year = validDate.getFullYear()
  const month = String(validDate.getMonth() + 1).padStart(2, '0')
  const day = String(validDate.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
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
  startDate,
  endDate,
  onCategoryChange,
  onStatusChange: _onStatusChange,
  onSourceChange,
  onAmountRangeChange,
  onDescriptionSearchChange,
  onDateRangeChange,
  onClearFilters,
}: TransactionFiltersProps) => {
  const [categoryInput, setCategoryInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const datePickerRef = useRef<HTMLDivElement>(null)
  const categoryContainerRef = useRef<HTMLDivElement>(null)
  const isAddingCategoryRef = useRef(false)

  // Date range state for RSuite DateRangePicker
  const [dateRange, setDateRange] = useState<[Date, Date] | null>(() => {
    if (startDate && endDate) {
      return [new Date(startDate), new Date(endDate)]
    }
    return null
  })

  // Update local date range when props change
  useEffect(() => {
    if (startDate && endDate) {
      setDateRange([new Date(startDate), new Date(endDate)])
    } else {
      setDateRange(null)
    }
  }, [startDate, endDate])

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
    selectedSourceId ||
    startDate ||
    endDate

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Don't close if clicking inside the date picker dropdown or category container
      const target = event.target as Node
      const isDatePickerClick = target && datePickerRef.current?.contains(target)
      const isCategoryClick = target && categoryContainerRef.current?.contains(target)
      const isDateRangeClick = target && (target as Element).closest?.('.rs-picker-popup, .date-picker-container')

      if (!isDatePickerClick && !isDateRangeClick && !isCategoryClick) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleDateRangeChange = useCallback(
    (range: [Date, Date] | null) => {
      setDateRange(range)

      if (range && range[0] && range[1] && onDateRangeChange) {
        const startDateStr = formatDateForInput(range[0])
        const endDateStr = formatDateForInput(range[1])
        onDateRangeChange(startDateStr, endDateStr)
      } else if (range === null && onDateRangeChange) {
        onDateRangeChange(undefined, undefined)
      }
    },
    [onDateRangeChange]
  )

  // Define predefined ranges for RSuite
  const predefinedRanges = [
    {
      label: 'Today',
      value: [new Date(), new Date()] as [Date, Date],
    },
    {
      label: 'Yesterday',
      value: (() => {
        const yesterday = new Date()
        yesterday.setDate(yesterday.getDate() - 1)
        return [yesterday, yesterday] as [Date, Date]
      })(),
    },
    {
      label: 'Last 7 Days',
      value: (() => {
        const end = new Date()
        const start = new Date()
        start.setDate(start.getDate() - 6)
        return [start, end] as [Date, Date]
      })(),
    },
    {
      label: 'Last 30 Days',
      value: (() => {
        const end = new Date()
        const start = new Date()
        start.setDate(start.getDate() - 29)
        return [start, end] as [Date, Date]
      })(),
    },
    {
      label: 'This Month',
      value: (() => {
        const now = new Date()
        const start = new Date(now.getFullYear(), now.getMonth(), 1)
        const end = new Date()
        return [start, end] as [Date, Date]
      })(),
    },
    {
      label: 'Last Month',
      value: (() => {
        const now = new Date()
        const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
        const end = new Date(now.getFullYear(), now.getMonth(), 0)
        return [start, end] as [Date, Date]
      })(),
    },
    {
      label: 'This Year',
      value: (() => {
        const now = new Date()
        const start = new Date(now.getFullYear(), 0, 1)
        const end = new Date()
        return [start, end] as [Date, Date]
      })(),
    },
    {
      label: 'Last Year',
      value: (() => {
        const now = new Date()
        const start = new Date(now.getFullYear() - 1, 0, 1)
        const end = new Date(now.getFullYear() - 1, 11, 31)
        return [start, end] as [Date, Date]
      })(),
    },
  ]

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
    // Show suggestions if there's input text - availableCategories will be recalculated
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
    <div className={`transaction-filters-advanced ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="filter-header">
        <h3>Filters</h3>
        <div className="filter-header-actions">
          {hasActiveFilters && (
            <button onClick={onClearFilters} className="clear-all-button">
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="collapse-toggle-button"
            aria-label={isCollapsed ? 'Expand filters' : 'Collapse filters'}
          >
            <span className={`collapse-chevron ${isCollapsed ? 'collapsed' : ''}`}>▼</span>
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="filters-grid">
          {/* Search Description */}
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

          {/* Date Range */}
          {onDateRangeChange && (
            <div className="filter-section">
              <label className="filter-label">Date Range</label>
              <div className="date-range-picker" ref={datePickerRef}>
                <DateRangePicker
                  value={dateRange}
                  onChange={handleDateRangeChange}
                  ranges={predefinedRanges}
                  placeholder="Select date range"
                  cleanable
                  showOneCalendar={false}
                  format="dd/MM/yyyy"
                  character=" - "
                  size="md"
                  placement="bottomStart"
                />
              </div>
            </div>
          )}

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

          {/* Categories - Full width */}
          <div className="filter-section filter-section-full-width">
            <label className="filter-label">Categories</label>

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
        </div>
      )}
    </div>
  )
}
