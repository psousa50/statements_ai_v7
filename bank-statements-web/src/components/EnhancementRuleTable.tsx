import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  IconButton,
  Chip,
  Box,
  Typography,
  CircularProgress,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import VisibilityIcon from '@mui/icons-material/Visibility'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import {
  EnhancementRule,
  EnhancementRuleFilters,
  EnhancementRuleSource,
  MatchType,
} from '../types/EnhancementRule'

interface EnhancementRuleTableProps {
  rules: EnhancementRule[]
  total: number
  filters: EnhancementRuleFilters
  loading: boolean
  onPageChange: (page: number) => void
  onSort: (field: string, direction: 'asc' | 'desc') => void
  onEdit: (rule: EnhancementRule) => void
  onDelete: (id: string) => void
}

export const EnhancementRuleTable: React.FC<EnhancementRuleTableProps> = ({
  rules,
  total,
  filters,
  loading,
  onPageChange,
  onSort,
  onEdit,
  onDelete,
}) => {
  const navigate = useNavigate()
  const handleSort = (field: string) => {
    const isAsc = filters.sort_field === field && filters.sort_direction === 'asc'
    onSort(field, isAsc ? 'desc' : 'asc')
  }

  const handlePageChange = (_: unknown, newPage: number) => {
    onPageChange(newPage + 1)
  }

  const handleViewTransactions = (rule: EnhancementRule) => {
    const params = new URLSearchParams({
      description_search: rule.normalized_description_pattern
    })
    navigate(`/transactions?${params.toString()}`)
  }

  const getMatchTypeLabel = (matchType: MatchType) => {
    switch (matchType) {
      case MatchType.EXACT:
        return 'Exact'
      case MatchType.PREFIX:
        return 'Prefix'
      case MatchType.INFIX:
        return 'Contains'
      default:
        return matchType
    }
  }

  const getMatchTypeColor = (matchType: MatchType) => {
    switch (matchType) {
      case MatchType.EXACT:
        return 'success'
      case MatchType.PREFIX:
        return 'warning'
      case MatchType.INFIX:
        return 'info'
      default:
        return 'default'
    }
  }

  const getRuleTypeDisplay = (rule: EnhancementRule) => {
    const hasCategory = rule.category_id
    const hasCounterparty = rule.counterparty_account_id

    if (hasCategory && hasCounterparty) {
      return 'Category + Counterparty'
    } else if (hasCategory) {
      return 'Category Only'
    } else if (hasCounterparty) {
      return 'Counterparty Only'
    }
    return 'Invalid Rule'
  }

  const getRuleTypeColor = (rule: EnhancementRule) => {
    const hasCategory = rule.category_id
    const hasCounterparty = rule.counterparty_account_id

    if (hasCategory && hasCounterparty) {
      return 'primary'
    } else if (hasCategory) {
      return 'secondary'
    } else if (hasCounterparty) {
      return 'info'
    }
    return 'error'
  }

  const formatConstraints = (rule: EnhancementRule) => {
    const constraints = []
    if (rule.min_amount !== null || rule.max_amount !== null) {
      if (rule.min_amount !== null && rule.max_amount !== null) {
        constraints.push(`Amount: €${rule.min_amount} - €${rule.max_amount}`)
      } else if (rule.min_amount !== null) {
        constraints.push(`Min: €${rule.min_amount}`)
      } else if (rule.max_amount !== null) {
        constraints.push(`Max: €${rule.max_amount}`)
      }
    }
    if (rule.start_date || rule.end_date) {
      if (rule.start_date && rule.end_date) {
        constraints.push(`Date: ${rule.start_date} - ${rule.end_date}`)
      } else if (rule.start_date) {
        constraints.push(`From: ${rule.start_date}`)
      } else if (rule.end_date) {
        constraints.push(`Until: ${rule.end_date}`)
      }
    }
    return constraints
  }

  if (loading && rules.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel
                  active={filters.sort_field === 'normalized_description_pattern'}
                  direction={
                    filters.sort_field === 'normalized_description_pattern' 
                      ? filters.sort_direction 
                      : 'asc'
                  }
                  onClick={() => handleSort('normalized_description_pattern')}
                >
                  Description
                </TableSortLabel>
              </TableCell>
              <TableCell>Match Type</TableCell>
              <TableCell>Rule Type</TableCell>
              <TableCell>
                <TableSortLabel
                  active={filters.sort_field === 'category'}
                  direction={
                    filters.sort_field === 'category' 
                      ? filters.sort_direction 
                      : 'asc'
                  }
                  onClick={() => handleSort('category')}
                >
                  Category
                </TableSortLabel>
              </TableCell>
              <TableCell>Counterparty</TableCell>
              <TableCell>Constraints</TableCell>
              <TableCell>
                <TableSortLabel
                  active={filters.sort_field === 'usage'}
                  direction={
                    filters.sort_field === 'usage' 
                      ? filters.sort_direction 
                      : 'asc'
                  }
                  onClick={() => handleSort('usage')}
                >
                  Usage
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={filters.sort_field === 'source'}
                  direction={
                    filters.sort_field === 'source' 
                      ? filters.sort_direction 
                      : 'asc'
                  }
                  onClick={() => handleSort('source')}
                >
                  Source
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={filters.sort_field === 'created_at'}
                  direction={
                    filters.sort_field === 'created_at' 
                      ? filters.sort_direction 
                      : 'asc'
                  }
                  onClick={() => handleSort('created_at')}
                >
                  Created
                </TableSortLabel>
              </TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id} hover>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {rule.normalized_description_pattern}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={getMatchTypeLabel(rule.match_type)}
                    color={getMatchTypeColor(rule.match_type) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={getRuleTypeDisplay(rule)}
                    color={getRuleTypeColor(rule) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {rule.category ? (
                    <Box>
                      <Typography variant="body2">
                        {rule.category.name}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {rule.counterparty_account ? (
                    <Typography variant="body2">
                      {rule.counterparty_account.name}
                      {rule.counterparty_account.account_number && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {rule.counterparty_account.account_number}
                        </Typography>
                      )}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {formatConstraints(rule).length > 0 ? (
                    <Box>
                      {formatConstraints(rule).map((constraint, index) => (
                        <Typography key={index} variant="caption" display="block">
                          {constraint}
                        </Typography>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">
                      {rule.transaction_count || 0}
                    </Typography>
                    {rule.transaction_count && rule.transaction_count > 0 && (
                      <IconButton
                        size="small"
                        onClick={() => handleViewTransactions(rule)}
                        title="View transactions"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={rule.source}
                    color={rule.source === EnhancementRuleSource.MANUAL ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(rule.created_at), 'MMM d, yyyy')}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton
                      size="small"
                      onClick={() => onEdit(rule)}
                      disabled={loading}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => onDelete(rule.id)}
                      disabled={loading}
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {rules.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No enhancement rules found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={total}
        page={(filters.page || 1) - 1}
        onPageChange={handlePageChange}
        rowsPerPage={filters.page_size || 50}
        rowsPerPageOptions={[25, 50, 100]}
        disabled={loading}
      />
    </>
  )
}