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
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import CleanupIcon from '@mui/icons-material/CleaningServices'
import { useEnhancementRules } from '../services/hooks/useEnhancementRules'
import { EnhancementRuleFilters, EnhancementRule, SortField } from '../types/EnhancementRule'
import { EnhancementRuleTable } from '../components/EnhancementRuleTable'
import { EnhancementRuleFiltersComponent } from '../components/EnhancementRuleFilters'
import { EnhancementRuleModal } from '../components/EnhancementRuleModal'
import { Pagination } from '../components/Pagination'
import './EnhancementRules.css'

export const EnhancementRules: React.FC = () => {
  const { loading, error, fetchRules, deleteRule, cleanupUnused } = useEnhancementRules()

  const [rules, setRules] = useState<EnhancementRule[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<EnhancementRuleFilters>({
    page: 1,
    page_size: 50,
    sort_field: 'usage',
    sort_direction: 'desc',
    show_invalid_only: true,
  })

  const [modalOpen, setModalOpen] = useState(false)
  const [selectedRule, setSelectedRule] = useState<EnhancementRule | null>(null)
  const [duplicateData, setDuplicateData] = useState<Partial<EnhancementRule> | null>(null)
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false)
  const [cleanupLoading, setCleanupLoading] = useState(false)

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
    </Box>
  )
}
