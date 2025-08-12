import React, { useState } from 'react'
import { Box, Typography, Paper, Switch, FormControlLabel, Button, Alert, Chip, Divider } from '@mui/material'
import { Add as AddIcon, FilterList as FilterIcon } from '@mui/icons-material'
import { FilterConditionRow } from './FilterConditionRow'

import { FilterOperator, LogicalOperator, FilterCondition, RowFilter } from '../../api/StatementClient'

// Re-export for convenience
export { FilterOperator, LogicalOperator }
export type { FilterCondition, RowFilter }

export interface FilterPreview {
  total_rows: number
  included_rows: number
  excluded_rows: number
  included_row_indices: number[]
  excluded_row_indices: number[]
}

interface RowFilterPanelProps {
  sampleData: string[][]
  columnMapping: Record<string, string>
  headerRowIndex: number
  dataStartRowIndex: number
  rowFilter: RowFilter | null
  onRowFilterChange: (filter: RowFilter | null) => void
  filterPreview?: FilterPreview | null
  suggestedFilters?: FilterCondition[]
  savedRowFilters?: FilterCondition[]
}

export const RowFilterPanel: React.FC<RowFilterPanelProps> = ({
  sampleData,
  columnMapping,
  headerRowIndex,
  dataStartRowIndex: _dataStartRowIndex,
  rowFilter,
  onRowFilterChange,
  filterPreview,
  suggestedFilters = [],
  savedRowFilters = [],
}) => {
  const [isEnabled, setIsEnabled] = useState(!!rowFilter)
  const [internalFilter, setInternalFilter] = useState<RowFilter>(() => {
    // Initialize with saved filters or default
    if (savedRowFilters && savedRowFilters.length > 0) {
      return {
        conditions: savedRowFilters,
        logical_operator: LogicalOperator.AND,
      }
    }
    if (rowFilter) {
      return rowFilter
    }
    // Default filter
    const defaultColumn = 'Column 1' // Will be updated when availableColumns is ready
    return {
      conditions: [
        {
          column_name: defaultColumn,
          operator: FilterOperator.CONTAINS,
          value: '',
          case_sensitive: false,
        },
      ],
      logical_operator: LogicalOperator.AND,
    }
  })

  // Auto-enable if we have saved filters
  React.useEffect(() => {
    if (savedRowFilters && savedRowFilters.length > 0) {
      setIsEnabled(true)
    }
  }, [savedRowFilters])

  // Notify parent only when enabled
  React.useEffect(() => {
    onRowFilterChange(isEnabled ? internalFilter : null)
  }, [isEnabled, internalFilter, onRowFilterChange])

  // Get available columns from the sample data and column mapping
  const availableColumns = React.useMemo(() => {
    if (!sampleData || sampleData.length <= headerRowIndex) return []

    const headerRow = sampleData[headerRowIndex] || []
    return headerRow.map((colName, index) => ({
      name: colName || `Column ${index + 1}`,
      index,
      isMapped: Object.values(columnMapping).includes(colName),
    }))
  }, [sampleData, headerRowIndex, columnMapping])

  const handleToggleFilter = (enabled: boolean) => {
    setIsEnabled(enabled)
    // The useEffect above will handle notifying the parent
  }

  const handleAddCondition = () => {
    const defaultColumn = availableColumns.length > 0 ? availableColumns[0].name : 'Column 1'
    const newCondition: FilterCondition = {
      column_name: defaultColumn,
      operator: FilterOperator.CONTAINS,
      value: '',
      case_sensitive: false,
    }

    setInternalFilter({
      ...internalFilter,
      conditions: [...internalFilter.conditions, newCondition],
    })
  }

  const handleRemoveCondition = (index: number) => {
    const newConditions = internalFilter.conditions.filter((_, i) => i !== index)

    if (newConditions.length === 0) {
      setIsEnabled(false)
    }

    setInternalFilter({
      ...internalFilter,
      conditions: newConditions,
    })
  }

  const handleConditionChange = (index: number, updatedCondition: FilterCondition) => {
    const newConditions = [...internalFilter.conditions]
    newConditions[index] = updatedCondition

    setInternalFilter({
      ...internalFilter,
      conditions: newConditions,
    })
  }

  const handleLogicalOperatorChange = (operator: LogicalOperator) => {
    setInternalFilter({
      ...internalFilter,
      logical_operator: operator,
    })
  }

  const applySuggestedFilter = (suggestion: FilterCondition) => {
    if (!isEnabled) {
      setIsEnabled(true)
    }

    setInternalFilter({
      conditions: [suggestion],
      logical_operator: LogicalOperator.AND,
    })
  }

  const getFilterSummary = () => {
    if (!filterPreview) return null

    const percentage =
      filterPreview.total_rows > 0 ? Math.round((filterPreview.included_rows / filterPreview.total_rows) * 100) : 0

    return `${filterPreview.included_rows} of ${filterPreview.total_rows} rows (${percentage}%) will be included`
  }

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FilterIcon sx={{ mr: 1 }} />
        <Typography variant="h6">Row Filters</Typography>
        <FormControlLabel
          control={<Switch checked={isEnabled} onChange={(e) => handleToggleFilter(e.target.checked)} />}
          label="Enable filtering"
          sx={{ ml: 'auto' }}
        />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Apply filters to exclude specific rows from your statement upload.
      </Typography>

      {/* Suggested Filters */}
      {suggestedFilters.length > 0 && (
        <Box sx={{ mb: 3, p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
            💡 Suggested filters:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {suggestedFilters.map((suggestion, index) => {
              const label =
                suggestion.operator === FilterOperator.IS_NOT_EMPTY
                  ? `Exclude empty ${suggestion.column_name}`
                  : `${suggestion.column_name} ${suggestion.operator.replace('_', ' ')} ${suggestion.value || ''}`.trim()

              return (
                <Chip
                  key={index}
                  label={label}
                  onClick={() => applySuggestedFilter(suggestion)}
                  variant="outlined"
                  size="small"
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'grey.100',
                      borderColor: 'grey.400',
                    },
                  }}
                />
              )
            })}
          </Box>
        </Box>
      )}

      {isEnabled && (
        <>
          <Divider sx={{ mb: 2 }} />

          {/* Filter Preview */}
          {filterPreview && (
            <Alert severity={filterPreview.included_rows > 0 ? 'info' : 'warning'} sx={{ mb: 2 }}>
              {getFilterSummary()}
            </Alert>
          )}

          {/* Filter Conditions */}
          <Box>
            {/* Logical Operator Selection (only show if multiple conditions) */}
            {internalFilter.conditions.length > 1 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Apply conditions using:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip
                    label="AND (all conditions must match)"
                    color={internalFilter.logical_operator === LogicalOperator.AND ? 'primary' : 'default'}
                    onClick={() => handleLogicalOperatorChange(LogicalOperator.AND)}
                    variant={internalFilter.logical_operator === LogicalOperator.AND ? 'filled' : 'outlined'}
                    sx={{ cursor: 'pointer' }}
                  />
                  <Chip
                    label="OR (any condition can match)"
                    color={internalFilter.logical_operator === LogicalOperator.OR ? 'primary' : 'default'}
                    onClick={() => handleLogicalOperatorChange(LogicalOperator.OR)}
                    variant={internalFilter.logical_operator === LogicalOperator.OR ? 'filled' : 'outlined'}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
              </Box>
            )}

            {/* Filter Conditions */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Filter conditions:
              </Typography>
              {internalFilter.conditions.map((condition, index) => (
                <FilterConditionRow
                  key={`condition-${index}`}
                  condition={condition}
                  availableColumns={availableColumns}
                  onConditionChange={(updatedCondition) => handleConditionChange(index, updatedCondition)}
                  onRemove={() => handleRemoveCondition(index)}
                  showRemoveButton={internalFilter.conditions.length > 1}
                />
              ))}
            </Box>

            {/* Add Condition Button */}
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddCondition}
              variant="outlined"
              size="medium"
              sx={{
                mt: 1,
                '&:hover': {
                  backgroundColor: 'primary.light',
                  borderColor: 'primary.main',
                },
              }}
            >
              Add Filter Condition
            </Button>
          </Box>
        </>
      )}
    </Paper>
  )
}
