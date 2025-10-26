import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  OutlinedInput,
  Button,
  Stack,
  SelectChangeEvent,
  FormControlLabel,
  Checkbox,
} from '@mui/material'
import ClearIcon from '@mui/icons-material/Clear'
import { useApi } from '../api/ApiContext'
import { EnhancementRuleFilters, EnhancementRuleSource, MatchType } from '../types/EnhancementRule'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface EnhancementRuleFiltersProps {
  filters: EnhancementRuleFilters
  onFiltersChange: (filters: EnhancementRuleFilters) => void
  loading?: boolean
}

interface CounterpartyAccount {
  id: string
  name: string
  account_number?: string
}

export const EnhancementRuleFiltersComponent: React.FC<EnhancementRuleFiltersProps> = ({
  filters,
  onFiltersChange,
  loading,
}) => {
  const apiClient = useApi()
  const [categories, setCategories] = useState<Category[]>([])
  const [counterpartyAccounts, setCounterpartyAccounts] = useState<CounterpartyAccount[]>([])
  const [localDescriptionSearch, setLocalDescriptionSearch] = useState(filters.description_search || '')

  const filtersRef = useRef(filters)
  const onFiltersChangeRef = useRef(onFiltersChange)

  // Keep refs updated
  filtersRef.current = filters
  onFiltersChangeRef.current = onFiltersChange

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await apiClient.categories.getAll()
        setCategories(response.categories)
      } catch (err) {
        console.error('Failed to load categories:', err)
      }
    }

    const loadCounterpartyAccounts = async () => {
      try {
        const response = await apiClient.accounts.getAll()
        setCounterpartyAccounts(response)
      } catch (err) {
        console.error('Failed to load counterparty accounts:', err)
      }
    }

    loadCategories()
    loadCounterpartyAccounts()
  }, [apiClient])

  // Debounce description search
  useEffect(() => {
    const timer = setTimeout(() => {
      const currentFilters = filtersRef.current
      const currentOnFiltersChange = onFiltersChangeRef.current

      // Only update if the description search value has actually changed
      if (currentFilters.description_search !== (localDescriptionSearch || undefined)) {
        currentOnFiltersChange({
          ...currentFilters,
          description_search: localDescriptionSearch || undefined,
        })
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [localDescriptionSearch])

  // Update local state when filters change externally (e.g., clear filters)
  useEffect(() => {
    setLocalDescriptionSearch(filters.description_search || '')
  }, [filters.description_search])

  const handleDescriptionSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLocalDescriptionSearch(event.target.value)
  }

  const handleCategoryChange = (categoryId?: string) => {
    onFiltersChange({
      ...filters,
      category_ids: categoryId ? [categoryId] : undefined,
    })
  }

  const handleCounterpartyChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    onFiltersChange({
      ...filters,
      counterparty_account_ids: typeof value === 'string' ? [] : value.length ? value : undefined,
    })
  }

  const handleMatchTypeChange = (event: SelectChangeEvent<string>) => {
    onFiltersChange({
      ...filters,
      match_type: event.target.value === '' ? undefined : (event.target.value as MatchType),
    })
  }

  const handleSourceChange = (event: SelectChangeEvent<string>) => {
    onFiltersChange({
      ...filters,
      source: event.target.value === '' ? undefined : (event.target.value as EnhancementRuleSource),
    })
  }

  const handleInvalidRulesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      show_invalid_only: event.target.checked ? true : undefined,
    })
  }

  const handleClearFilters = () => {
    onFiltersChange({
      page: 1,
      page_size: filters.page_size,
      sort_field: filters.sort_field,
      sort_direction: filters.sort_direction,
    })
  }

  const hasActiveFilters =
    filters.description_search ||
    filters.category_ids?.length ||
    filters.counterparty_account_ids?.length ||
    filters.match_type ||
    filters.source ||
    filters.show_invalid_only

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
        <Box sx={{ minWidth: 200 }}>
          <TextField
            fullWidth
            label="Search Description"
            variant="outlined"
            size="small"
            value={localDescriptionSearch}
            onChange={handleDescriptionSearchChange}
          />
        </Box>

        <Box sx={{ minWidth: 150 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Match Type</InputLabel>
            <Select
              value={filters.match_type || ''}
              onChange={handleMatchTypeChange}
              disabled={loading}
              label="Match Type"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value={MatchType.EXACT}>Exact</MenuItem>
              <MenuItem value={MatchType.PREFIX}>Prefix</MenuItem>
              <MenuItem value={MatchType.INFIX}>Infix</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ minWidth: 120 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Source</InputLabel>
            <Select value={filters.source || ''} onChange={handleSourceChange} disabled={loading} label="Source">
              <MenuItem value="">All</MenuItem>
              <MenuItem value={EnhancementRuleSource.MANUAL}>Manual</MenuItem>
              <MenuItem value={EnhancementRuleSource.AI}>AI</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ minWidth: 200 }}>
          <CategorySelector
            categories={categories}
            selectedCategoryId={filters.category_ids?.[0]}
            onCategoryChange={handleCategoryChange}
            placeholder="Select category"
            allowClear={true}
            multiple={false}
            variant="filter"
          />
        </Box>

        <Box sx={{ minWidth: 200 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Counterparties</InputLabel>
            <Select
              multiple
              value={filters.counterparty_account_ids || []}
              onChange={handleCounterpartyChange}
              input={<OutlinedInput label="Counterparties" />}
              disabled={loading}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => {
                    const account = counterpartyAccounts.find((a) => a.id === value)
                    return <Chip key={value} label={account?.name || value} size="small" />
                  })}
                </Box>
              )}
            >
              {counterpartyAccounts.map((account) => (
                <MenuItem key={account.id} value={account.id}>
                  {account.name}
                  {account.account_number && ` (${account.account_number})`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={filters.show_invalid_only || false}
                onChange={handleInvalidRulesChange}
                disabled={loading}
                size="small"
              />
            }
            label="Show Unconfigured Rules Only"
          />
        </Box>

        {hasActiveFilters && (
          <Box>
            <Button
              variant="outlined"
              size="small"
              startIcon={<ClearIcon />}
              onClick={handleClearFilters}
              disabled={loading}
            >
              Clear Filters
            </Button>
          </Box>
        )}
      </Stack>
    </Box>
  )
}
