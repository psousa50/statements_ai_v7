import { useState, useCallback } from 'react'
import { Category, Account } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import { DatePeriodNavigator } from './DatePeriodNavigator'
import { FilterPreset } from '../api/FilterPresetClient'

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
  transactionTypeDisabled?: boolean
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
  filterPresets?: FilterPreset[]
  filterPresetsLoading?: boolean
  currentPresetName?: string
  onSavePreset?: (name: string, isRelative: boolean) => Promise<void>
  onLoadPreset?: (preset: FilterPreset) => void
  onDeletePreset?: (presetId: string) => Promise<void>
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
  transactionTypeDisabled = false,
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
  filterPresets = [],
  filterPresetsLoading = false,
  currentPresetName,
  onSavePreset,
  onLoadPreset,
  onDeletePreset,
}: TransactionFiltersProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [presetName, setPresetName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [isRelative, setIsRelative] = useState(true)

  const hasDateFilter = Boolean(startDate || endDate)

  const handleOpenSaveModal = useCallback(() => {
    setPresetName(currentPresetName || '')
    setShowSaveModal(true)
  }, [currentPresetName])

  const categoryIds = selectedCategoryIds ?? []

  const hasActiveFilters =
    categoryIds.length > 0 ||
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

  const handleSavePreset = useCallback(async () => {
    if (!onSavePreset || !presetName.trim()) return
    setIsSaving(true)
    try {
      await onSavePreset(presetName.trim(), hasDateFilter && isRelative)
      setPresetName('')
      setShowSaveModal(false)
      setIsRelative(true)
    } finally {
      setIsSaving(false)
    }
  }, [onSavePreset, presetName, hasDateFilter, isRelative])

  const handleLoadPreset = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const presetId = e.target.value
      if (!presetId || !onLoadPreset) return
      const preset = filterPresets.find((p) => p.id === presetId)
      if (preset) {
        onLoadPreset(preset)
      }
      e.target.value = ''
    },
    [filterPresets, onLoadPreset]
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
          {onLoadPreset && (
            <div className="preset-dropdown-container">
              <select
                className="preset-dropdown"
                onChange={handleLoadPreset}
                disabled={filterPresetsLoading || filterPresets.length === 0}
                value={filterPresets.find((p) => p.name === currentPresetName)?.id ?? ''}
              >
                <option value="" disabled>
                  {filterPresetsLoading ? 'Loading...' : 'Load preset...'}
                </option>
                {filterPresets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </select>
              {onDeletePreset && currentPresetName && (
                <button
                  className="preset-delete-button"
                  onClick={() => {
                    const preset = filterPresets.find((p) => p.name === currentPresetName)
                    if (preset) onDeletePreset(preset.id)
                  }}
                  title="Delete current preset"
                >
                  🗑
                </button>
              )}
            </div>
          )}
          {onSavePreset && hasActiveFilters && (
            <button onClick={handleOpenSaveModal} className="save-preset-button">
              Save
            </button>
          )}
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

            <div className="filter-group categories-group">
              <label className="filter-label">Categories</label>
              <CategorySelector
                categories={categories}
                selectedCategoryIds={categoryIds}
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

            <div className="filter-group">
              <label htmlFor="transaction-type-filter" className="filter-label">
                Type
              </label>
              <select
                id="transaction-type-filter"
                value={transactionType}
                onChange={(e) => onTransactionTypeChange(e.target.value as 'all' | 'debit' | 'credit')}
                className="filter-input filter-select"
                disabled={transactionTypeDisabled}
              >
                <option value="all">All</option>
                <option value="debit">Debits</option>
                <option value="credit">Credits</option>
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

      {onDateRangeChange && (
        <div className="date-range-row">
          <DatePeriodNavigator
            key={`${startDate}-${endDate}`}
            startDate={startDate}
            endDate={endDate}
            onChange={onDateRangeChange}
            defaultPeriodType="all"
          />
        </div>
      )}

      {showSaveModal && (
        <div className="save-preset-modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="save-preset-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Save Filter Preset</h4>
            <input
              type="text"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="Preset name..."
              className="preset-name-input"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter' && presetName.trim()) {
                  handleSavePreset()
                } else if (e.key === 'Escape') {
                  setShowSaveModal(false)
                }
              }}
            />
            {hasDateFilter && (
              <div className="date-type-selection">
                <p className="date-type-label">Date range type:</p>
                <label className="date-type-option">
                  <input type="radio" name="dateType" checked={isRelative} onChange={() => setIsRelative(true)} />
                  <span className="date-type-text">
                    <strong>Rolling window</strong>
                    <small>Dates shift forward automatically over time</small>
                  </span>
                </label>
                <label className="date-type-option">
                  <input type="radio" name="dateType" checked={!isRelative} onChange={() => setIsRelative(false)} />
                  <span className="date-type-text">
                    <strong>Fixed dates</strong>
                    <small>Dates stay exactly as selected</small>
                  </span>
                </label>
              </div>
            )}
            <div className="save-preset-modal-actions">
              <button onClick={() => setShowSaveModal(false)} className="cancel-button" disabled={isSaving}>
                Cancel
              </button>
              <button onClick={handleSavePreset} className="save-button" disabled={!presetName.trim() || isSaving}>
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
