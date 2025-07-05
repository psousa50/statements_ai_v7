import { useState, useCallback, useRef, useEffect } from 'react'
import { DateRangePicker } from 'rsuite'
import { CategorizationStatus, Category, Account } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import 'rsuite/dist/rsuite.min.css'

interface TransactionFiltersProps {
  categories: Category[]
  accounts: Account[]
  selectedCategoryIds?: string[]
  selectedStatus?: CategorizationStatus
  selectedAccountId?: string
  minAmount?: number
  maxAmount?: number
  descriptionSearch?: string
  startDate?: string
  endDate?: string
  excludeTransfers?: boolean
  onCategoryChange: (categoryIds: string[]) => void
  onStatusChange: (status?: CategorizationStatus) => void
  onAccountChange: (accountId?: string) => void
  onAmountRangeChange: (minAmount?: number, maxAmount?: number) => void
  onDescriptionSearchChange: (search?: string) => void
  onDateRangeChange?: (startDate?: string, endDate?: string) => void
  onExcludeTransfersChange: (excludeTransfers: boolean) => void
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
  accounts,
  selectedCategoryIds = [],
  selectedStatus,
  selectedAccountId,
  minAmount,
  maxAmount,
  descriptionSearch,
  startDate,
  endDate,
  excludeTransfers,
  onCategoryChange,
  onStatusChange: _onStatusChange,
  onAccountChange,
  onAmountRangeChange,
  onDescriptionSearchChange,
  onDateRangeChange,
  onExcludeTransfersChange,
  onClearFilters,
}: TransactionFiltersProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const datePickerRef = useRef<HTMLDivElement>(null)

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

  const hasActiveFilters =
    selectedCategoryIds.length > 0 ||
    selectedStatus ||
    minAmount !== undefined ||
    maxAmount !== undefined ||
    descriptionSearch ||
    selectedAccountId ||
    startDate ||
    endDate ||
    excludeTransfers === false // Only consider it active if explicitly set to false

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
        <div className="filters-container">
          {/* Primary Filters Row */}
          <div className="filters-row primary-filters">
            {/* Search */}
            <div className="filter-group search-group">
              <label htmlFor="description-search" className="filter-label">
                Search
              </label>
              <input
                id="description-search"
                type="text"
                value={descriptionSearch || ''}
                onChange={(e) => onDescriptionSearchChange(e.target.value || undefined)}
                placeholder="Search transactions..."
                className="filter-input search-input"
              />
            </div>

            {/* Date Range */}
            <div className="filter-group date-group">
              <label className="filter-label">Date Range</label>
              {onDateRangeChange ? (
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
                    className="date-range-picker-input"
                  />
                </div>
              ) : (
                <div className="filter-placeholder">
                  Not available
                </div>
              )}
            </div>
          </div>

          {/* Secondary Filters Row */}
          <div className="filters-row secondary-filters">
            {/* Status */}
            <div className="filter-group">
              <label htmlFor="status-filter" className="filter-label">
                Status
              </label>
              <select
                id="status-filter"
                value={selectedStatus || ''}
                onChange={(e) => _onStatusChange((e.target.value as CategorizationStatus) || undefined)}
                className="filter-input filter-select"
              >
                <option value="">All Statuses</option>
                <option value="CATEGORIZED">Categorized</option>
                <option value="UNCATEGORIZED">Uncategorized</option>
              </select>
            </div>

            {/* Account */}
            <div className="filter-group">
              <label htmlFor="account-filter" className="filter-label">
                Account
              </label>
              <select
                id="account-filter"
                value={selectedAccountId || ''}
                onChange={(e) => onAccountChange(e.target.value || undefined)}
                className="filter-input filter-select"
              >
                <option value="">All Accounts</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Amount Range */}
            <div className="filter-group amount-group">
              <label className="filter-label">Amount Range</label>
              <div className="amount-range-inputs">
                <input
                  type="number"
                  value={minAmount ?? ''}
                  onChange={(e) => handleAmountChange('min', e.target.value)}
                  placeholder="Min"
                  className="filter-input amount-input"
                  step="0.01"
                />
                <span className="amount-separator">to</span>
                <input
                  type="number"
                  value={maxAmount ?? ''}
                  onChange={(e) => handleAmountChange('max', e.target.value)}
                  placeholder="Max"
                  className="filter-input amount-input"
                  step="0.01"
                />
              </div>
            </div>

            {/* Options */}
            <div className="filter-group options-group">
              <label className="filter-label">Options</label>
              <div className="checkbox-container">
                <label htmlFor="exclude-transfers" className="checkbox-label">
                  <input
                    id="exclude-transfers"
                    type="checkbox"
                    checked={excludeTransfers !== false}
                    onChange={(e) => onExcludeTransfersChange(e.target.checked)}
                    className="checkbox-input"
                  />
                  <span className="checkbox-text">Exclude Transfers</span>
                </label>
              </div>
            </div>
          </div>

          {/* Categories Row - Full width */}
          <div className="filters-row categories-row">
            <div className="filter-group categories-group">
              <label className="filter-label">Categories</label>
              <CategorySelector
                categories={categories}
                selectedCategoryIds={selectedCategoryIds}
                onCategoryChange={() => {}} // Not used in multiple mode
                onCategoryIdsChange={onCategoryChange}
                placeholder="Type to add categories..."
                multiple={true}
                allowClear={false}
                variant="filter"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
