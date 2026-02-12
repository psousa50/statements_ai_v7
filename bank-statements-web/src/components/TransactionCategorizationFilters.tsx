import { Category } from '../types/Transaction'
import { CategorizationSource } from '../types/TransactionCategorization'
import { CategorySelector } from './CategorySelector'
import { StyledSelect } from './StyledSelect'

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
  const hasActiveFilters = selectedCategoryIds.length > 0 || selectedSource || descriptionSearch

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
          <StyledSelect
            id="source-filter"
            value={selectedSource || ''}
            onChange={(v) => onSourceChange((v as CategorizationSource) || undefined)}
            options={[
              { value: '', label: 'All Sources' },
              { value: CategorizationSource.MANUAL, label: 'Manual' },
              { value: CategorizationSource.AI, label: 'AI' },
            ]}
          />
        </div>

        {/* Categories */}
        <div className="filter-section filter-section-categories">
          <CategorySelector
            categories={categories}
            selectedCategoryIds={selectedCategoryIds}
            onCategoryIdsChange={onCategoryChange}
            placeholder="Type to add categories..."
            multiple={true}
            allowClear={false}
            onCategoryChange={() => {}}
          />
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
