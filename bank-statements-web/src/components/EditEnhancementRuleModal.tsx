import React, { useState, useEffect } from 'react'
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
} from '@mui/material'
import { useApi } from '../api/ApiContext'
import { useEnhancementRules } from '../services/hooks/useEnhancementRules'
import {
  EnhancementRule,
  EnhancementRuleUpdate,
  EnhancementRuleSource,
  MatchType,
} from '../types/EnhancementRule'
import { Category } from '../types/Transaction'

interface EditEnhancementRuleModalProps {
  open: boolean
  rule: EnhancementRule
  onClose: () => void
  onSuccess: () => void
}

interface CounterpartyAccount {
  id: string
  name: string
  account_number?: string
}

export const EditEnhancementRuleModal: React.FC<EditEnhancementRuleModalProps> = ({
  open,
  rule,
  onClose,
  onSuccess,
}) => {
  const apiClient = useApi()
  const { updateRule, loading, error } = useEnhancementRules()
  
  const [categories, setCategories] = useState<Category[]>([])
  const [counterpartyAccounts, setCounterpartyAccounts] = useState<CounterpartyAccount[]>([])
  const [formData, setFormData] = useState<EnhancementRuleUpdate>({
    normalized_description_pattern: '',
    match_type: MatchType.INFIX,
    source: EnhancementRuleSource.MANUAL,
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (rule) {
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
    }
  }, [rule])

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

  const validateForm = () => {
    const errors: Record<string, string> = {}

    if (!formData.normalized_description_pattern.trim()) {
      errors.normalized_description_pattern = 'Description is required'
    }

    if (!formData.category_id && !formData.counterparty_account_id) {
      errors.rule_type = 'Must specify either a category, counterparty, or both'
    }

    if (formData.min_amount !== undefined && formData.max_amount !== undefined) {
      if (formData.min_amount > formData.max_amount) {
        errors.amount_range = 'Minimum amount cannot be greater than maximum amount'
      }
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
      await updateRule(rule.id, formData)
      onSuccess()
      handleClose()
    } catch (err) {
      console.error('Failed to update enhancement rule:', err)
    }
  }

  const handleClose = () => {
    setValidationErrors({})
    onClose()
  }

  const handleFieldChange = (field: keyof EnhancementRuleUpdate, value: any) => {
    setFormData({ ...formData, [field]: value })
    if (validationErrors[field]) {
      setValidationErrors({ ...validationErrors, [field]: '' })
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit Enhancement Rule</DialogTitle>
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
              <FormHelperText>
                How to match the description pattern
              </FormHelperText>
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
            {validationErrors.rule_type && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {validationErrors.rule_type}
              </Alert>
            )}
          </Box>

          <Stack direction="row" spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Category (Optional)</InputLabel>
              <Select
                value={formData.category_id || ''}
                label="Category (Optional)"
                onChange={(e) => handleFieldChange('category_id', e.target.value || undefined)}
              >
                <MenuItem value="">None</MenuItem>
                {categories.map((category) => (
                  <MenuItem key={category.id} value={category.id}>
                    {category.name}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>
                Category to assign to matching transactions
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
              <FormHelperText>
                Counterparty to assign to matching transactions
              </FormHelperText>
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
              helperText={validationErrors.amount_range || "Only apply rule to transactions below this amount"}
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
              helperText={validationErrors.date_range || "Only apply rule to transactions before this date"}
              InputLabelProps={{
                shrink: true,
              }}
            />
          </Stack>
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
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}