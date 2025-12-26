import { useState, useCallback } from 'react'
import { Category, Account } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import { DatePeriodNavigator } from './DatePeriodNavigator'

export type CategorizationFilter = 'all' | 'categorized' | 'uncategorized'

interface TransactionFiltersProps {
  categories: Category[]
  accounts: Account[]
  selectedCategoryIds?: string[]
  selectedAccountId?: string
  minAmount?: number
  maxAmount?: number
  descriptionSearch?: string
  startDate?: string
  endDate?: string
  excludeTransfers?: boolean
  categorizationFilter?: CategorizationFilter
  hideUncategorizedOnlyOption?: boolean
  transactionType?: 'all' | 'debit' | 'credit'
  defaultTransactionType?: 'all' | 'debit' | 'credit'
  defaultCategorizationFilter?: CategorizationFilter
  defaultExcludeTransfers?: boolean
  onCategoryChange: (categoryIds: string[]) => void
  onAccountChange: (accountId?: string) => void
  onAmountRangeChange: (minAmount?: number, maxAmount?: number) => void
  onDescriptionSearchChange: (search?: string) => void
  onDateRangeChange?: (startDate?: string, endDate?: string) => void
  onExcludeTransfersChange: (excludeTransfers: boolean) => void
  onCategorizationFilterChange: (filter: CategorizationFilter) => void
  onTransactionTypeChange: (type: 'all' | 'debit' | 'credit') => void
  onClearFilters: () => void
}

export const TransactionFilters = ({
  categories,
  accounts,
  selectedCategoryIds = [],
  selectedAccountId,
  minAmount,
  maxAmount,
  descriptionSearch,
  startDate,
  endDate,
  excludeTransfers,
  categorizationFilter = 'all',
  hideUncategorizedOnlyOption = false,
  transactionType = 'all',
  defaultTransactionType = 'all',
  defaultCategorizationFilter = 'all',
  defaultExcludeTransfers = true,
  onCategoryChange,
  onAccountChange,
  onAmountRangeChange,
  onDescriptionSearchChange,
  onDateRangeChange,
  onExcludeTransfersChange,
  onCategorizationFilterChange,
  onTransactionTypeChange,
  onClearFilters,
}: TransactionFiltersProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const hasActiveFilters =
    selectedCategoryIds.length > 0 ||
    minAmount !== undefined ||
    maxAmount !== undefined ||
    descriptionSearch ||
    selectedAccountId ||
    excludeTransfers !== defaultExcludeTransfers ||
    categorizationFilter !== defaultCategorizationFilter ||
    transactionType !== defaultTransactionType

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

  const handleHeaderClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.filter-header-actions')) {
      return
    }
    setIsCollapsed(!isCollapsed)
  }

  return (
    <div className={`transaction-filters-advanced ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="filter-header" onClick={handleHeaderClick}>
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
          <div className="filters-row primary-filters">
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

            <div className="filter-group date-group">
              <label className="filter-label">Date Range</label>
              {onDateRangeChange ? (
                <DatePeriodNavigator
                  startDate={startDate}
                  endDate={endDate}
                  onChange={onDateRangeChange}
                  defaultPeriodType="month"
                />
              ) : (
                <div className="filter-placeholder">Not available</div>
              )}
            </div>

            <div className="filter-group categories-group">
              <label className="filter-label">Categories</label>
              <CategorySelector
                categories={categories}
                selectedCategoryIds={selectedCategoryIds}
                onCategoryChange={() => {}}
                onCategoryIdsChange={onCategoryChange}
                placeholder="Type to add categories..."
                multiple={true}
                allowClear={false}
                variant="filter"
              />
            </div>
          </div>

          <div className="filters-row secondary-filters">
            <div className="filter-group">
              <label htmlFor="transaction-type-filter" className="filter-label">
                Type
              </label>
              <select
                id="transaction-type-filter"
                value={transactionType}
                onChange={(e) => onTransactionTypeChange(e.target.value as 'all' | 'debit' | 'credit')}
                className="filter-input filter-select"
              >
                <option value="all">All</option>
                <option value="debit">Debits</option>
                <option value="credit">Credits</option>
              </select>
            </div>

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

            <div className="filter-group amount-group">
              <label className="filter-label">Amount</label>
              <div className="amount-range-inputs">
                <input
                  type="number"
                  value={minAmount ?? ''}
                  onChange={(e) => handleAmountChange('min', e.target.value)}
                  placeholder="Min"
                  className="filter-input amount-input"
                  step="0.01"
                />
                <span className="amount-separator">–</span>
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

            <div className="filter-group">
              <label htmlFor="categorization-filter" className="filter-label">
                Status
              </label>
              <select
                id="categorization-filter"
                value={categorizationFilter}
                onChange={(e) => onCategorizationFilterChange(e.target.value as CategorizationFilter)}
                className="filter-input filter-select"
              >
                <option value="all">All</option>
                <option value="categorized">Categorised</option>
                {!hideUncategorizedOnlyOption && <option value="uncategorized">Uncategorised</option>}
              </select>
            </div>

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
        </div>
      )}
    </div>
  )
}
