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
import { EnhancementRuleFilters, EnhancementRule } from '../types/EnhancementRule'
import { EnhancementRuleTable } from '../components/EnhancementRuleTable'
import { EnhancementRuleFiltersComponent } from '../components/EnhancementRuleFilters'
import { CreateEnhancementRuleModal } from '../components/CreateEnhancementRuleModal'
import { EditEnhancementRuleModal } from '../components/EditEnhancementRuleModal'

export const EnhancementRules: React.FC = () => {
  const {
    loading,
    error,
    fetchRules,
    deleteRule,
    cleanupUnused,
  } = useEnhancementRules()

  const [rules, setRules] = useState<EnhancementRule[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<EnhancementRuleFilters>({
    page: 1,
    page_size: 50,
    sort_field: 'created_at',
    sort_direction: 'desc',
  })

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedRule, setSelectedRule] = useState<EnhancementRule | null>(null)
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

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setFilters({
      ...filters,
      sort_field: field as any,
      sort_direction: direction,
      page: 1,
    })
  }

  const handleCreateRule = () => {
    setCreateModalOpen(true)
  }

  const handleEditRule = (rule: EnhancementRule) => {
    setSelectedRule(rule)
    setEditModalOpen(true)
  }

  const handleDeleteRule = async (id: string) => {
    try {
      await deleteRule(id)
      await loadRules()
    } catch (err) {
      console.error('Failed to delete enhancement rule:', err)
    }
  }

  const handleRuleCreated = () => {
    setCreateModalOpen(false)
    loadRules()
  }

  const handleRuleUpdated = () => {
    setEditModalOpen(false)
    setSelectedRule(null)
    loadRules()
  }

  const handleCleanupUnused = async () => {
    setCleanupLoading(true)
    try {
      const result = await cleanupUnused()
      setCleanupDialogOpen(false)
      await loadRules()
      // You might want to show a success message here
      console.log(`Cleanup completed: ${result.message}`)
    } catch (err) {
      console.error('Failed to cleanup unused rules:', err)
    } finally {
      setCleanupLoading(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
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
            startIcon={<CleanupIcon />}
            onClick={() => setCleanupDialogOpen(true)}
          >
            Cleanup Unused
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateRule}
          >
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
        <EnhancementRuleFiltersComponent
          filters={filters}
          onFiltersChange={handleFiltersChange}
          loading={loading}
        />
      </Paper>

      <Paper sx={{ p: 0 }}>
        <EnhancementRuleTable
          rules={rules}
          total={total}
          filters={filters}
          loading={loading}
          onPageChange={handlePageChange}
          onSort={handleSort}
          onEdit={handleEditRule}
          onDelete={handleDeleteRule}
        />
      </Paper>

      {/* Create Rule Modal */}
      <CreateEnhancementRuleModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={handleRuleCreated}
      />

      {/* Edit Rule Modal */}
      {selectedRule && (
        <EditEnhancementRuleModal
          open={editModalOpen}
          rule={selectedRule}
          onClose={() => {
            setEditModalOpen(false)
            setSelectedRule(null)
          }}
          onSuccess={handleRuleUpdated}
        />
      )}

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialogOpen} onClose={() => setCleanupDialogOpen(false)}>
        <DialogTitle>Cleanup Unused Rules</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete all enhancement rules that haven't been used to categorize
            any transactions. This action cannot be undone.
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