import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Snackbar,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import CleanupIcon from '@mui/icons-material/CleaningServices'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { useEnhancementRules } from '../services/hooks/useEnhancementRules'
import {
  EnhancementRuleFilters,
  EnhancementRule,
  SortField,
  AISuggestCategoriesResponse,
} from '../types/EnhancementRule'
import { EnhancementRuleTable } from '../components/EnhancementRuleTable'
import { EnhancementRuleFiltersComponent } from '../components/EnhancementRuleFilters'
import { EnhancementRuleModal } from '../components/EnhancementRuleModal'
import { Pagination } from '../components/Pagination'
import './EnhancementRules.css'

export const EnhancementRules: React.FC = () => {
  const {
    loading,
    error,
    fetchRules,
    deleteRule,
    cleanupUnused,
    suggestCategories,
    applySuggestion,
    rejectSuggestion,
  } = useEnhancementRules()

  const [rules, setRules] = useState<EnhancementRule[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<EnhancementRuleFilters>({
    page: 1,
    page_size: 50,
    sort_field: 'usage',
    sort_direction: 'desc',
    rule_status_filter: 'unconfigured',
  })

  const [modalOpen, setModalOpen] = useState(false)
  const [selectedRule, setSelectedRule] = useState<EnhancementRule | null>(null)
  const [duplicateData, setDuplicateData] = useState<Partial<EnhancementRule> | null>(null)
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false)
  const [cleanupLoading, setCleanupLoading] = useState(false)
  const [aiDialogOpen, setAiDialogOpen] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const loadRules = async () => {
    try {
      const response = await fetchRules(filters)
      setRules(response.rules)
      setTotal(response.total)
    } catch (err) {
      console.error('Failed to load enhancement rules:', err)
    }
  }

  useEffect(() => {
    loadRules()
  }, [filters])

  const handleFiltersChange = (newFilters: EnhancementRuleFilters) => {
    setFilters({ ...newFilters, page: 1 })
  }

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page })
  }

  const handlePageSizeChange = (page_size: number) => {
    setFilters({ ...filters, page_size, page: 1 })
  }

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setFilters({
      ...filters,
      sort_field: field as SortField,
      sort_direction: direction,
      page: 1,
    })
  }

  const handleCreateRule = () => {
    setSelectedRule(null) // Clear selected rule for create mode
    setModalOpen(true)
  }

  const handleEditRule = (rule: EnhancementRule) => {
    setSelectedRule(rule)
    setModalOpen(true)
  }

  const handleDuplicateRule = (rule: EnhancementRule) => {
    const duplicatedData = {
      normalized_description_pattern: rule.normalized_description_pattern,
      match_type: rule.match_type,
      category_id: rule.category_id,
      counterparty_account_id: rule.counterparty_account_id,
      min_amount: rule.min_amount,
      max_amount: rule.max_amount,
      start_date: rule.start_date,
      end_date: rule.end_date,
      source: rule.source,
    }
    setSelectedRule(null) // No rule selected, this is a new rule
    setDuplicateData(duplicatedData) // Pass the data to duplicate
    setModalOpen(true)
  }

  const handleDeleteRule = async (id: string) => {
    try {
      await deleteRule(id)
      await loadRules()
    } catch (err) {
      console.error('Failed to delete enhancement rule:', err)
    }
  }

  const handleModalSuccess = () => {
    setModalOpen(false)
    setSelectedRule(null)
    setDuplicateData(null)
    loadRules()
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setSelectedRule(null)
    setDuplicateData(null)
  }

  const handleCleanupUnused = async () => {
    setCleanupLoading(true)
    try {
      await cleanupUnused()
      setCleanupDialogOpen(false)
      await loadRules()
    } catch (err) {
      console.error('Failed to cleanup unused rules:', err)
    } finally {
      setCleanupLoading(false)
    }
  }

  const handleAISuggest = async () => {
    setAiLoading(true)
    try {
      const result = await suggestCategories({
        confidence_threshold: 0.8,
        auto_apply: true,
      })
      setAiDialogOpen(false)
      await loadRules()

      const message =
        result.auto_applied > 0
          ? `${result.auto_applied} rules auto-categorised, ${result.suggestions} need review`
          : result.suggestions > 0
            ? `${result.suggestions} suggestions ready for review`
            : result.processed === 0
              ? 'No unconfigured rules to process'
              : result.failed > 0
                ? `AI failed to categorise ${result.failed} rules (check API key)`
                : 'No suggestions generated'

      setSnackbar({
        open: true,
        message,
        severity: result.auto_applied > 0 || result.suggestions > 0 ? 'success' : 'error',
      })
    } catch (err) {
      console.error('Failed to suggest categories:', err)
      setSnackbar({
        open: true,
        message: 'Failed to generate AI suggestions',
        severity: 'error',
      })
    } finally {
      setAiLoading(false)
    }
  }

  const handleApplySuggestion = async (ruleId: string, applyToTransactions: boolean) => {
    try {
      await applySuggestion(ruleId, { apply_to_transactions: applyToTransactions })
      await loadRules()
      setSnackbar({
        open: true,
        message: 'Suggestion applied successfully',
        severity: 'success',
      })
    } catch (err) {
      console.error('Failed to apply suggestion:', err)
      setSnackbar({
        open: true,
        message: 'Failed to apply suggestion',
        severity: 'error',
      })
    }
  }

  const handleRejectSuggestion = async (ruleId: string) => {
    try {
      await rejectSuggestion(ruleId)
      await loadRules()
    } catch (err) {
      console.error('Failed to reject suggestion:', err)
    }
  }

  return (
    <Box sx={{ p: 3 }} className="enhancement-rules-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Typography variant="h4" component="h1">
          Enhancement Rules
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => setAiDialogOpen(true)}
          >
            AI Suggest
          </Button>
          <Button variant="outlined" startIcon={<CleanupIcon />} onClick={() => setCleanupDialogOpen(true)}>
            Cleanup Unused
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreateRule}>
            Create Rule
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <EnhancementRuleFiltersComponent filters={filters} onFiltersChange={handleFiltersChange} loading={loading} />
      </Paper>

      <Paper sx={{ p: 0 }}>
        <EnhancementRuleTable
          rules={rules}
          filters={filters}
          loading={loading}
          onSort={handleSort}
          onEdit={handleEditRule}
          onDuplicate={handleDuplicateRule}
          onDelete={handleDeleteRule}
          onApplySuggestion={handleApplySuggestion}
          onRejectSuggestion={handleRejectSuggestion}
        />
      </Paper>

      {!loading && total > 0 && (
        <Paper sx={{ p: 0 }}>
          <div className="transactions-pagination">
            <Pagination
              currentPage={filters.page || 1}
              totalPages={Math.ceil(total / (filters.page_size || 50))}
              totalItems={total}
              pageSize={filters.page_size || 50}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              itemName="rules"
            />
          </div>
        </Paper>
      )}

      {/* Enhancement Rule Modal (Create/Edit) */}
      <EnhancementRuleModal
        open={modalOpen}
        rule={selectedRule || undefined}
        duplicateData={duplicateData || undefined}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
      />

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialogOpen} onClose={() => setCleanupDialogOpen(false)}>
        <DialogTitle>Cleanup Unused Rules</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete all enhancement rules that haven't been used to categorize any transactions.
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCleanupDialogOpen(false)} disabled={cleanupLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleCleanupUnused}
            color="error"
            variant="contained"
            disabled={cleanupLoading}
            startIcon={cleanupLoading ? <CircularProgress size={16} /> : <CleanupIcon />}
          >
            {cleanupLoading ? 'Cleaning...' : 'Cleanup'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Suggestion Dialog */}
      <Dialog open={aiDialogOpen} onClose={() => setAiDialogOpen(false)}>
        <DialogTitle>AI Category Suggestions</DialogTitle>
        <DialogContent>
          <Typography>
            AI will analyse unconfigured rules and suggest categories based on the transaction description patterns.
          </Typography>
          <Typography sx={{ mt: 2, color: 'text.secondary', fontSize: '0.875rem' }}>
            Rules with high confidence (80%+) will be auto-applied. Lower confidence suggestions will need your review.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAiDialogOpen(false)} disabled={aiLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleAISuggest}
            color="secondary"
            variant="contained"
            disabled={aiLoading}
            startIcon={aiLoading ? <CircularProgress size={16} /> : <AutoAwesomeIcon />}
          >
            {aiLoading ? 'Analysing...' : 'Generate Suggestions'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
