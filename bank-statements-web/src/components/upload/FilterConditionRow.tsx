import React from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  IconButton,
  FormControlLabel,
  Checkbox,
  Tooltip,
  SelectChangeEvent,
  ListSubheader,
} from '@mui/material'
import { Delete as DeleteIcon, Info as InfoIcon } from '@mui/icons-material'
import type { FilterCondition } from '../../api/StatementClient'
import { FilterOperator } from '../../api/StatementClient'

interface FilterConditionRowProps {
  condition: FilterCondition
  availableColumns: { name: string; index: number; isMapped: boolean }[]
  onConditionChange: (updatedCondition: FilterCondition) => void
  onRemove: () => void
  showRemoveButton?: boolean
}

export const FilterConditionRow: React.FC<FilterConditionRowProps> = ({
  condition,
  availableColumns,
  onConditionChange,
  onRemove,
  showRemoveButton = true,
}) => {
  // Operators that don't require a value
  const NO_VALUE_OPERATORS = [FilterOperator.IS_EMPTY, FilterOperator.IS_NOT_EMPTY]
  
  // Operators that work with text
  const TEXT_OPERATORS = [
    FilterOperator.CONTAINS,
    FilterOperator.NOT_CONTAINS,
    FilterOperator.EQUALS,
    FilterOperator.NOT_EQUALS,
    FilterOperator.REGEX,
  ]
  
  // Operators that work with numbers
  const NUMERIC_OPERATORS = [
    FilterOperator.GREATER_THAN,
    FilterOperator.LESS_THAN,
    FilterOperator.GREATER_THAN_OR_EQUAL,
    FilterOperator.LESS_THAN_OR_EQUAL,
  ]

  const getOperatorLabel = (operator: FilterOperator): string => {
    switch (operator) {
      case FilterOperator.CONTAINS:
        return 'Contains'
      case FilterOperator.NOT_CONTAINS:
        return 'Does not contain'
      case FilterOperator.EQUALS:
        return 'Equals'
      case FilterOperator.NOT_EQUALS:
        return 'Does not equal'
      case FilterOperator.GREATER_THAN:
        return 'Greater than'
      case FilterOperator.LESS_THAN:
        return 'Less than'
      case FilterOperator.GREATER_THAN_OR_EQUAL:
        return 'Greater than or equal'
      case FilterOperator.LESS_THAN_OR_EQUAL:
        return 'Less than or equal'
      case FilterOperator.REGEX:
        return 'Matches regex'
      case FilterOperator.IS_EMPTY:
        return 'Is empty'
      case FilterOperator.IS_NOT_EMPTY:
        return 'Is not empty'
      default:
        return operator
    }
  }

  const getOperatorTooltip = (operator: FilterOperator): string => {
    switch (operator) {
      case FilterOperator.CONTAINS:
        return 'Row will be included if the column contains this text'
      case FilterOperator.NOT_CONTAINS:
        return 'Row will be included if the column does not contain this text'
      case FilterOperator.EQUALS:
        return 'Row will be included if the column exactly matches this value'
      case FilterOperator.NOT_EQUALS:
        return 'Row will be included if the column does not match this value'
      case FilterOperator.GREATER_THAN:
        return 'Row will be included if the column value is greater than this number'
      case FilterOperator.LESS_THAN:
        return 'Row will be included if the column value is less than this number'
      case FilterOperator.GREATER_THAN_OR_EQUAL:
        return 'Row will be included if the column value is greater than or equal to this number'
      case FilterOperator.LESS_THAN_OR_EQUAL:
        return 'Row will be included if the column value is less than or equal to this number'
      case FilterOperator.REGEX:
        return 'Row will be included if the column matches this regular expression'
      case FilterOperator.IS_EMPTY:
        return 'Row will be included if the column is empty or contains only whitespace'
      case FilterOperator.IS_NOT_EMPTY:
        return 'Row will be included if the column has any content'
      default:
        return ''
    }
  }

  const handleColumnChange = (event: SelectChangeEvent) => {
    onConditionChange({
      ...condition,
      column_name: event.target.value,
    })
  }

  const handleOperatorChange = (event: SelectChangeEvent) => {
    const newOperator = event.target.value as FilterOperator
    onConditionChange({
      ...condition,
      operator: newOperator,
      // Clear value if the new operator doesn't need one
      value: NO_VALUE_OPERATORS.includes(newOperator) ? undefined : condition.value,
    })
  }

  const handleValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onConditionChange({
      ...condition,
      value: event.target.value,
    })
  }

  const handleCaseSensitiveChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onConditionChange({
      ...condition,
      case_sensitive: event.target.checked,
    })
  }

  const needsValue = !NO_VALUE_OPERATORS.includes(condition.operator)
  const isTextOperator = TEXT_OPERATORS.includes(condition.operator)
  const isNumericOperator = NUMERIC_OPERATORS.includes(condition.operator)

  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 2, 
      p: 2, 
      border: 1, 
      borderColor: 'divider', 
      borderRadius: 2,
      mb: 2,
      backgroundColor: 'background.paper',
      flexWrap: { xs: 'wrap', md: 'nowrap' },
      '&:hover': {
        borderColor: 'primary.main',
        boxShadow: 1,
      }
    }}>
      {/* Column Selection */}
      <FormControl sx={{ minWidth: 150 }}>
        <InputLabel>Column</InputLabel>
        <Select
          value={condition.column_name}
          label="Column"
          onChange={handleColumnChange}
          size="small"
        >
          {availableColumns.map((column) => (
            <MenuItem 
              key={column.index} 
              value={column.name}
              sx={{ 
                fontWeight: column.isMapped ? 'bold' : 'normal',
                color: column.isMapped ? 'primary.main' : 'text.primary'
              }}
            >
              {column.name}
              {column.isMapped && ' ✓'}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Operator Selection */}
      <FormControl sx={{ minWidth: 180 }}>
        <InputLabel>Condition</InputLabel>
        <Select
          value={condition.operator}
          label="Condition"
          onChange={handleOperatorChange}
          size="small"
        >
          <ListSubheader>Text Operations</ListSubheader>
          {TEXT_OPERATORS.map((operator) => (
            <MenuItem key={operator} value={operator}>
              {getOperatorLabel(operator)}
            </MenuItem>
          ))}
          
          <ListSubheader>Numeric Operations</ListSubheader>
          {NUMERIC_OPERATORS.map((operator) => (
            <MenuItem key={operator} value={operator}>
              {getOperatorLabel(operator)}
            </MenuItem>
          ))}
          
          <ListSubheader>Empty Check</ListSubheader>
          {[FilterOperator.IS_EMPTY, FilterOperator.IS_NOT_EMPTY].map((operator) => (
            <MenuItem key={operator} value={operator}>
              {getOperatorLabel(operator)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Value Input */}
      {needsValue && (
        <TextField
          label="Value"
          value={condition.value || ''}
          onChange={handleValueChange}
          size="small"
          sx={{ minWidth: 120 }}
          type={isNumericOperator ? 'number' : 'text'}
          placeholder={
            isNumericOperator 
              ? 'Enter number' 
              : condition.operator === FilterOperator.REGEX 
                ? 'Enter regex pattern'
                : 'Enter text'
          }
        />
      )}

      {/* Case Sensitive Checkbox (only for text operations) */}
      {needsValue && isTextOperator && (
        <FormControlLabel
          control={
            <Checkbox
              checked={condition.case_sensitive}
              onChange={handleCaseSensitiveChange}
              size="small"
            />
          }
          label="Case sensitive"
        />
      )}

      {/* Info Tooltip */}
      <Tooltip title={getOperatorTooltip(condition.operator)} arrow>
        <InfoIcon color="action" fontSize="small" sx={{ cursor: 'help' }} />
      </Tooltip>

      {/* Remove Button */}
      {showRemoveButton && (
        <IconButton
          onClick={onRemove}
          color="error"
          size="small"
          sx={{ 
            ml: 'auto',
            '&:hover': {
              backgroundColor: 'error.light',
              color: 'error.contrastText',
            }
          }}
        >
          <DeleteIcon />
        </IconButton>
      )}
    </Box>
  )
}