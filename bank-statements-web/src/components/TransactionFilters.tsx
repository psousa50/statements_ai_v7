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
    startDate ||
    endDate ||
    excludeTransfers === false ||
    categorizationFilter !== 'all' ||
    transactionType !== 'all'

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
          </div>

          {/* Secondary Filters Row */}
          <div className="filters-row secondary-filters">
            {/* Transaction Type */}
            <div className="filter-group">
              <label htmlFor="transaction-type-filter" className="filter-label">
                Transaction Type
              </label>
              <select
                id="transaction-type-filter"
                value={transactionType}
                onChange={(e) => onTransactionTypeChange(e.target.value as 'all' | 'debit' | 'credit')}
                className="filter-input filter-select"
              >
                <option value="all">All Transactions</option>
                <option value="debit">Debits Only</option>
                <option value="credit">Credits Only</option>
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

            {/* Categorization Filter */}
            <div className="filter-group">
              <label htmlFor="categorization-filter" className="filter-label">
                Categorization
              </label>
              <select
                id="categorization-filter"
                value={categorizationFilter}
                onChange={(e) => onCategorizationFilterChange(e.target.value as CategorizationFilter)}
                className="filter-input filter-select"
              >
                <option value="all">All</option>
                <option value="categorized">Categorized only</option>
                {!hideUncategorizedOnlyOption && <option value="uncategorized">Uncategorized only</option>}
              </select>
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
