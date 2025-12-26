import React, { useState, useEffect, useRef } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Alert,
  CircularProgress,
  FormHelperText,
  Typography,
  Box,
  Checkbox,
  FormControlLabel,
} from '@mui/material'
import { useApi } from '../api/ApiContext'
import { useEnhancementRules } from '../services/hooks/useEnhancementRules'
import {
  EnhancementRule,
  EnhancementRuleCreate,
  EnhancementRuleUpdate,
  EnhancementRuleSource,
  MatchType,
  MatchingTransactionsCountResponse,
} from '../types/EnhancementRule'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface EnhancementRuleModalProps {
  open: boolean
  rule?: EnhancementRule // undefined for create, defined for edit
  duplicateData?: Partial<EnhancementRule> // data to pre-fill when duplicating
  onClose: () => void
  onSuccess: () => void
}

interface CounterpartyAccount {
  id: string
  name: string
  account_number?: string
}

export const EnhancementRuleModal: React.FC<EnhancementRuleModalProps> = ({
  open,
  rule,
  duplicateData,
  onClose,
  onSuccess,
}) => {
  const apiClient = useApi()
  const { createRule, updateRule, loading, error } = useEnhancementRules()

  const isEditing = !!rule?.id
  const [categories, setCategories] = useState<Category[]>([])
  const [counterpartyAccounts, setCounterpartyAccounts] = useState<CounterpartyAccount[]>([])
  const [formData, setFormData] = useState<EnhancementRuleCreate | EnhancementRuleUpdate>({
    normalized_description_pattern: '',
    match_type: MatchType.INFIX,
    source: EnhancementRuleSource.MANUAL,
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // State for retroactive application
  const [applyToExisting, setApplyToExisting] = useState(false)
  const [matchingCount, setMatchingCount] = useState<MatchingTransactionsCountResponse | null>(null)
  const [fetchingCount, setFetchingCount] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)

  // State for creating empty copy
  const [createEmptyCopy, setCreateEmptyCopy] = useState(true)

  // Debounce timeout for preview updates
  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  // Initialize form data when rule or duplicateData changes
  useEffect(() => {
    if (rule) {
      // Editing existing rule
      setFormData({
        normalized_description_pattern: rule.normalized_description_pattern,
        match_type: rule.match_type,
        category_id: rule.category_id,
        counterparty_account_id: rule.counterparty_account_id,
        min_amount: rule.min_amount,
        max_amount: rule.max_amount,
        start_date: rule.start_date,
        end_date: rule.end_date,
        source: rule.source,
      })
    } else if (duplicateData) {
      // Creating new rule from duplicate data
      setFormData({
        normalized_description_pattern: duplicateData.normalized_description_pattern || '',
        match_type: duplicateData.match_type || MatchType.INFIX,
        category_id: duplicateData.category_id,
        counterparty_account_id: duplicateData.counterparty_account_id,
        min_amount: duplicateData.min_amount,
        max_amount: duplicateData.max_amount,
        start_date: duplicateData.start_date,
        end_date: duplicateData.end_date,
        source: duplicateData.source || EnhancementRuleSource.MANUAL,
      })
    } else {
      // Reset form for create mode
      setFormData({
        normalized_description_pattern: '',
        match_type: MatchType.INFIX,
        source: EnhancementRuleSource.MANUAL,
      })
    }
  }, [rule, duplicateData])

  useEffect(() => {
    const loadData = async () => {
      try {
        const [categoriesResponse, accountsResponse] = await Promise.all([
          apiClient.categories.getAll(),
          apiClient.accounts.getAll(),
        ])
        setCategories(categoriesResponse.categories)
        setCounterpartyAccounts(accountsResponse)
      } catch (err) {
        console.error('Failed to load data:', err)
      }
    }

    if (open) {
      loadData()
    }
  }, [open, apiClient])

  // Smart auto-check logic: check apply_to_existing when category or counterparty changes
  useEffect(() => {
    if (!isEditing || !rule) return

    const categoryChanged = formData.category_id !== rule.category_id
    const counterpartyChanged = formData.counterparty_account_id !== rule.counterparty_account_id

    // Auto-check if significant changes are made
    if (categoryChanged || counterpartyChanged) {
      setApplyToExisting(true)
    }
  }, [formData.category_id, formData.counterparty_account_id, isEditing, rule])

  // Simple preview effect: always use preview endpoint for everything
  useEffect(() => {
    // Only run if modal is open and we have a valid description
    if (!open || !formData.normalized_description_pattern.trim()) {
      setMatchingCount(null)
      return
    }

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Set debounced timeout
    debounceTimeoutRef.current = setTimeout(async () => {
      setFetchingCount(true)
      setPreviewError(null)
      try {
        const count = await apiClient.enhancementRules.previewMatchingTransactionsCount(formData)
        setMatchingCount(count)
      } catch (err) {
        setMatchingCount(null)
        setPreviewError(err instanceof Error ? err.message : 'Failed to fetch preview')
      } finally {
        setFetchingCount(false)
      }
    }, 500)

    // Cleanup on unmount or dependency change
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [
    open,
    formData.normalized_description_pattern,
    formData.match_type,
    formData.category_id,
    formData.counterparty_account_id,
    formData.min_amount,
    formData.max_amount,
    formData.start_date,
    formData.end_date,
    apiClient,
  ])

  const hasConstraints = () => {
    return !!(
      (formData.min_amount !== undefined && formData.min_amount !== null) ||
      (formData.max_amount !== undefined && formData.max_amount !== null) ||
      formData.start_date ||
      formData.end_date
    )
  }

  const validateForm = () => {
    const errors: Record<string, string> = {}

    if (!formData.normalized_description_pattern.trim()) {
      errors.normalized_description_pattern = 'Description is required'
    }

    if (
      typeof formData.min_amount === 'number' &&
      typeof formData.max_amount === 'number' &&
      formData.min_amount > formData.max_amount
    ) {
      errors.amount_range = 'Minimum amount cannot be greater than maximum amount'
    }

    if (formData.start_date && formData.end_date) {
      if (new Date(formData.start_date) > new Date(formData.end_date)) {
        errors.date_range = 'Start date cannot be after end date'
      }
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) {
      return
    }

    try {
      if (isEditing && rule) {
        const updateData: EnhancementRuleUpdate = {
          ...formData,
          apply_to_existing: applyToExisting,
        }
        await updateRule(rule.id, updateData)
      } else {
        // Clean the data by removing null and undefined values
        const cleanedData: EnhancementRuleCreate = {
          normalized_description_pattern: formData.normalized_description_pattern,
          match_type: formData.match_type,
          source: formData.source,
        }

        // Only add optional fields if they have valid values
        if (formData.category_id) {
          cleanedData.category_id = formData.category_id
        }
        if (formData.counterparty_account_id) {
          cleanedData.counterparty_account_id = formData.counterparty_account_id
        }
        if (formData.min_amount !== undefined && formData.min_amount !== null) {
          cleanedData.min_amount = formData.min_amount
        }
        if (formData.max_amount !== undefined && formData.max_amount !== null) {
          cleanedData.max_amount = formData.max_amount
        }
        if (formData.start_date) {
          cleanedData.start_date = formData.start_date
        }
        if (formData.end_date) {
          cleanedData.end_date = formData.end_date
        }

        await createRule(cleanedData)
      }

      if (createEmptyCopy && hasConstraints()) {
        const emptyCopyData: EnhancementRuleCreate = {
          normalized_description_pattern: formData.normalized_description_pattern,
          match_type: formData.match_type,
          source: formData.source,
        }
        await createRule(emptyCopyData)
      }

      onSuccess()
      handleClose()
    } catch (err) {
      console.error(`Failed to ${isEditing ? 'update' : 'create'} enhancement rule:`, err)
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response: { data: unknown; status: number } }
        console.error('Error response data:', axiosError.response.data)
        console.error('Error response status:', axiosError.response.status)
      }
    }
  }

  const handleClose = () => {
    if (!isEditing) {
      // Reset form only for create mode
      setFormData({
        normalized_description_pattern: '',
        match_type: MatchType.INFIX,
        source: EnhancementRuleSource.MANUAL,
      })
    }
    setValidationErrors({})

    // Reset retroactive application state
    setApplyToExisting(false)
    setMatchingCount(null)
    setFetchingCount(false)
    setPreviewError(null)

    // Reset empty copy state
    setCreateEmptyCopy(true)

    onClose()
  }

  const handleFieldChange = (
    field: keyof (EnhancementRuleCreate | EnhancementRuleUpdate),
    value: string | number | boolean | undefined
  ) => {
    setFormData({ ...formData, [field]: value })
    if (validationErrors[field]) {
      setValidationErrors({ ...validationErrors, [field]: '' })
    }
  }

  const handleCreateCategory = async (name: string, parentId?: string) => {
    try {
      const newCategory = await apiClient.categories.create({ name, parent_id: parentId })
      setCategories((prev) => [...prev, newCategory].sort((a, b) => a.name.localeCompare(b.name)))
      return newCategory
    } catch (error) {
      console.error('Failed to create category:', error)
      return null
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{isEditing ? 'Edit Enhancement Rule' : 'Create Enhancement Rule'}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            label="Description Pattern"
            value={formData.normalized_description_pattern}
            onChange={(e) => handleFieldChange('normalized_description_pattern', e.target.value)}
            error={!!validationErrors.normalized_description_pattern}
            helperText={
              validationErrors.normalized_description_pattern ||
              'Enter the text pattern to match in transaction descriptions'
            }
            required
            autoFocus={!isEditing}
          />

          <Stack direction="row" spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Match Type *</InputLabel>
              <Select
                value={formData.match_type}
                label="Match Type *"
                onChange={(e) => handleFieldChange('match_type', e.target.value)}
              >
                <MenuItem value={MatchType.EXACT}>Exact Match</MenuItem>
                <MenuItem value={MatchType.PREFIX}>Starts With (Prefix)</MenuItem>
                <MenuItem value={MatchType.INFIX}>Contains (Infix)</MenuItem>
              </Select>
              <FormHelperText>How to match the description pattern</FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Source</InputLabel>
              <Select
                value={formData.source}
                label="Source"
                onChange={(e) => handleFieldChange('source', e.target.value)}
              >
                <MenuItem value={EnhancementRuleSource.MANUAL}>Manual</MenuItem>
                <MenuItem value={EnhancementRuleSource.AI}>AI</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          <Box>
            <Typography variant="h6" gutterBottom>
              Rule Actions
            </Typography>
          </Box>

          <Stack direction="row" spacing={2}>
            <FormControl fullWidth>
              <CategorySelector
                categories={categories}
                selectedCategoryId={formData.category_id}
                onCategoryChange={(categoryId) => handleFieldChange('category_id', categoryId)}
                placeholder="Category (Optional)"
                allowClear={true}
                multiple={false}
                variant="form"
                autoFocus={isEditing}
                allowCreate={true}
                onCategoryCreate={handleCreateCategory}
              />
              <FormHelperText>
                Category to assign to matching transactions. Type "Parent &gt; Child" to create a subcategory.
              </FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Counterparty Account (Optional)</InputLabel>
              <Select
                value={formData.counterparty_account_id || ''}
                label="Counterparty Account (Optional)"
                onChange={(e) => handleFieldChange('counterparty_account_id', e.target.value || undefined)}
              >
                <MenuItem value="">None</MenuItem>
                {counterpartyAccounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    {account.name}
                    {account.account_number && ` (${account.account_number})`}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>Counterparty to assign to matching transactions</FormHelperText>
            </FormControl>
          </Stack>

          <Box>
            <Typography variant="h6" gutterBottom>
              Constraints (Optional)
            </Typography>
          </Box>

          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              label="Minimum Amount"
              type="number"
              value={formData.min_amount || ''}
              onChange={(e) => handleFieldChange('min_amount', e.target.value ? parseFloat(e.target.value) : undefined)}
              error={!!validationErrors.amount_range}
              helperText="Only apply rule to transactions above this amount"
            />

            <TextField
              fullWidth
              label="Maximum Amount"
              type="number"
              value={formData.max_amount || ''}
              onChange={(e) => handleFieldChange('max_amount', e.target.value ? parseFloat(e.target.value) : undefined)}
              error={!!validationErrors.amount_range}
              helperText={validationErrors.amount_range || 'Only apply rule to transactions below this amount'}
            />
          </Stack>

          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              label="Start Date"
              type="date"
              value={formData.start_date || ''}
              onChange={(e) => handleFieldChange('start_date', e.target.value || undefined)}
              error={!!validationErrors.date_range}
              helperText="Only apply rule to transactions after this date"
              InputLabelProps={{
                shrink: true,
              }}
            />

            <TextField
              fullWidth
              label="End Date"
              type="date"
              value={formData.end_date || ''}
              onChange={(e) => handleFieldChange('end_date', e.target.value || undefined)}
              error={!!validationErrors.date_range}
              helperText={validationErrors.date_range || 'Only apply rule to transactions before this date'}
              InputLabelProps={{
                shrink: true,
              }}
            />
          </Stack>

          {/* Single unified preview section */}
          {(fetchingCount || matchingCount || previewError) && (
            <>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Rule Preview
                </Typography>
              </Box>

              {/* Show loading state */}
              {fetchingCount && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <CircularProgress size={16} />
                    <Typography variant="body2">Checking for matching transactions...</Typography>
                  </Stack>
                </Alert>
              )}

              {/* Show error */}
              {!fetchingCount && previewError && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  ❌ Preview failed: {previewError}
                  <br />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    You may need to select a category or counterparty account for the rule to work.
                  </Typography>
                </Alert>
              )}

              {/* Show results */}
              {!fetchingCount && !previewError && matchingCount && (
                <Alert
                  severity={isEditing && applyToExisting && matchingCount.count > 0 ? 'warning' : 'info'}
                  sx={{ mt: 1 }}
                >
                  {matchingCount.count > 0 ? (
                    <>
                      {isEditing && applyToExisting ? '⚠️' : '📊'} This rule would{' '}
                      {isEditing && applyToExisting ? 'update' : 'match'} <strong>{matchingCount.count}</strong>{' '}
                      existing transactions.
                      <br />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {isEditing && applyToExisting
                          ? "Only transactions that haven't been manually categorized will be updated."
                          : isEditing
                            ? 'These transactions could be updated if you apply changes to existing transactions.'
                            : 'These transactions will be enhanced when you create this rule.'}
                      </Typography>
                    </>
                  ) : (
                    <>
                      📊 No existing transactions match this rule pattern.
                      <br />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        This rule will only apply to future transactions.
                      </Typography>
                    </>
                  )}
                </Alert>
              )}
            </>
          )}

          {/* Retroactive Application Section - only show in edit mode */}
          {isEditing && (
            <>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Apply to Existing Transactions
                </Typography>
              </Box>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={applyToExisting}
                    onChange={(e) => setApplyToExisting(e.target.checked)}
                    disabled={loading}
                  />
                }
                label="Apply these changes to existing matching transactions"
              />
            </>
          )}

          {/* Empty Copy Section - show when constraints exist */}
          {hasConstraints() && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Create Additional Rule
              </Typography>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={createEmptyCopy}
                    onChange={(e) => setCreateEmptyCopy(e.target.checked)}
                    disabled={loading}
                  />
                }
                label="Also create an unconstrained copy of this rule (same pattern, no amount/date filters)"
              />
              <FormHelperText sx={{ mt: -1, ml: 4 }}>
                This creates a second rule that matches all transactions with this pattern, useful for catching edge
                cases outside your specified constraints.
              </FormHelperText>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : undefined}
        >
          {loading
            ? isEditing
              ? 'Saving...'
              : 'Creating...'
            : isEditing
              ? applyToExisting && matchingCount && matchingCount.count > 0
                ? `Save & Apply to ${matchingCount.count} Transactions`
                : 'Save Changes'
              : 'Create Rule'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
