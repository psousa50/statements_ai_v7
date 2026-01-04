import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  IconButton,
  Chip,
  Box,
  Typography,
  CircularProgress,
  Tooltip,
  Button,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import VisibilityIcon from '@mui/icons-material/Visibility'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CheckIcon from '@mui/icons-material/Check'
import CloseIcon from '@mui/icons-material/Close'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { EnhancementRule, EnhancementRuleFilters, EnhancementRuleSource, MatchType } from '../types/EnhancementRule'

interface EnhancementRuleTableProps {
  rules: EnhancementRule[]
  filters: EnhancementRuleFilters
  loading: boolean
  onSort: (field: string, direction: 'asc' | 'desc') => void
  onEdit: (rule: EnhancementRule) => void
  onDuplicate: (rule: EnhancementRule) => void
  onDelete: (id: string) => void
  onApply?: (rule: EnhancementRule) => void
  onApplySuggestion?: (ruleId: string, applyToTransactions: boolean) => void
  onRejectSuggestion?: (ruleId: string) => void
}

export const EnhancementRuleTable: React.FC<EnhancementRuleTableProps> = ({
  rules,
  filters,
  loading,
  onSort,
  onEdit,
  onDuplicate,
  onDelete,
  onApply,
  onApplySuggestion,
  onRejectSuggestion,
}) => {
  const handleSort = (field: string) => {
    const isAsc = filters.sort_field === field && filters.sort_direction === 'asc'
    onSort(field, isAsc ? 'desc' : 'asc')
  }

  const handleViewTransactions = (rule: EnhancementRule) => {
    const isUnconfigured = !rule.category_id && !rule.counterparty_account_id
    const params = new URLSearchParams({
      enhancement_rule_id: rule.id,
    })
    if (isUnconfigured) {
      params.set('status', 'UNCATEGORIZED')
    }
    window.open(`/transactions?${params.toString()}`, '_blank')
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

  const getMatchTypeColor = (
    matchType: MatchType
  ): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
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

  const getRuleTypeColor = (
    ruleType: string
  ): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (ruleType) {
      case 'Category + Counterparty':
        return 'primary'
      case 'Category Only':
        return 'secondary'
      case 'Counterparty Only':
        return 'info'
      case 'Unconfigured':
        return 'error'
      default:
        return 'default'
    }
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
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              <TableSortLabel
                active={filters.sort_field === 'normalized_description_pattern'}
                direction={filters.sort_field === 'normalized_description_pattern' ? filters.sort_direction : 'asc'}
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
                direction={filters.sort_field === 'category' ? filters.sort_direction : 'asc'}
                onClick={() => handleSort('category')}
              >
                Category
              </TableSortLabel>
            </TableCell>
            <TableCell>Counterparty</TableCell>
            <TableCell>Constraints</TableCell>
            <TableCell align="right">
              <TableSortLabel
                active={filters.sort_field === 'usage'}
                direction={filters.sort_field === 'usage' ? filters.sort_direction : 'asc'}
                onClick={() => handleSort('usage')}
              >
                Usage
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel
                active={filters.sort_field === 'latest_match'}
                direction={filters.sort_field === 'latest_match' ? filters.sort_direction : 'desc'}
                onClick={() => handleSort('latest_match')}
              >
                Latest Match
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel
                active={filters.sort_field === 'source'}
                direction={filters.sort_field === 'source' ? filters.sort_direction : 'asc'}
                onClick={() => handleSort('source')}
              >
                Source
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ width: '120px' }}>Actions</TableCell>
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
                  color={getMatchTypeColor(rule.match_type)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip label={rule.rule_type} color={getRuleTypeColor(rule.rule_type)} size="small" />
              </TableCell>
              <TableCell>
                {rule.category ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {rule.ai_suggested_category_id === rule.category_id && (
                      <Tooltip title="Set by AI">
                        <AutoAwesomeIcon sx={{ fontSize: 14, color: 'secondary.main' }} />
                      </Tooltip>
                    )}
                    <Box>
                      {rule.category.parent && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {rule.category.parent.name}
                        </Typography>
                      )}
                      <Typography variant="body2">{rule.category.name}</Typography>
                    </Box>
                  </Box>
                ) : rule.ai_suggested_category ? (
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 0.5,
                      p: 1,
                      borderRadius: 1,
                      bgcolor: 'action.hover',
                      border: '1px dashed',
                      borderColor: 'secondary.main',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AutoAwesomeIcon sx={{ fontSize: 14, color: 'secondary.main' }} />
                      <Box>
                        {rule.ai_suggested_category.parent && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {rule.ai_suggested_category.parent.name}
                          </Typography>
                        )}
                        <Typography variant="body2" color="secondary.main">
                          {rule.ai_suggested_category.name}
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {Math.round((rule.ai_category_confidence ?? 0) * 100)}% confidence
                    </Typography>
                    {onApplySuggestion && onRejectSuggestion && (
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<CheckIcon sx={{ fontSize: 14 }} />}
                          onClick={() => onApplySuggestion(rule.id, true)}
                          sx={{ fontSize: '0.7rem', py: 0.25, px: 1, minWidth: 'auto' }}
                        >
                          Accept
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          startIcon={<CloseIcon sx={{ fontSize: 14 }} />}
                          onClick={() => onRejectSuggestion(rule.id)}
                          sx={{ fontSize: '0.7rem', py: 0.25, px: 1, minWidth: 'auto' }}
                        >
                          Reject
                        </Button>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    —
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {rule.counterparty_account ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {rule.ai_suggested_counterparty_id === rule.counterparty_account_id && (
                      <Tooltip title="Set by AI">
                        <AutoAwesomeIcon sx={{ fontSize: 14, color: 'info.main' }} />
                      </Tooltip>
                    )}
                    <Box>
                      <Typography variant="body2">{rule.counterparty_account.name}</Typography>
                      {rule.counterparty_account.account_number && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {rule.counterparty_account.account_number}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                ) : rule.ai_suggested_counterparty ? (
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 0.5,
                      p: 1,
                      borderRadius: 1,
                      bgcolor: 'action.hover',
                      border: '1px dashed',
                      borderColor: 'info.main',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AutoAwesomeIcon sx={{ fontSize: 14, color: 'info.main' }} />
                      <Typography variant="body2" color="info.main">
                        {rule.ai_suggested_counterparty.name}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {Math.round((rule.ai_counterparty_confidence ?? 0) * 100)}% confidence
                    </Typography>
                    {onApplySuggestion && onRejectSuggestion && (
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<CheckIcon sx={{ fontSize: 14 }} />}
                          onClick={() => onApplySuggestion(rule.id, true)}
                          sx={{ fontSize: '0.7rem', py: 0.25, px: 1, minWidth: 'auto' }}
                        >
                          Accept
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          startIcon={<CloseIcon sx={{ fontSize: 14 }} />}
                          onClick={() => onRejectSuggestion(rule.id)}
                          sx={{ fontSize: '0.7rem', py: 0.25, px: 1, minWidth: 'auto' }}
                        >
                          Reject
                        </Button>
                      </Box>
                    )}
                  </Box>
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
              <TableCell align="right">
                {rule.category_id ? (
                  <Typography
                    variant="body2"
                    color={(rule.pending_transaction_count ?? 0) === 0 ? 'success.main' : 'text.primary'}
                  >
                    {rule.pending_transaction_count ?? 0} / {rule.transaction_count ?? 0}
                  </Typography>
                ) : (
                  <Typography variant="body2">{rule.transaction_count ?? 0}</Typography>
                )}
              </TableCell>
              <TableCell>
                {rule.latest_match_date ? (
                  <Typography variant="body2">
                    {new Date(rule.latest_match_date).toLocaleDateString('en-GB', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    —
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Chip
                  label={rule.source}
                  color={rule.source === EnhancementRuleSource.MANUAL ? 'primary' : 'secondary'}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex !important', gap: '0 !important', width: 'fit-content' }}>
                  <IconButton
                    size="small"
                    onClick={() => handleViewTransactions(rule)}
                    title="View transactions"
                    sx={{
                      minWidth: '0 !important',
                      padding: '4px !important',
                      margin: '0 !important',
                      width: '24px !important',
                      height: '24px !important',
                      visibility: (rule.transaction_count ?? 0) > 0 ? 'visible' : 'hidden',
                    }}
                  >
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onEdit(rule)}
                    disabled={loading}
                    title="Edit rule"
                    sx={{
                      minWidth: '0 !important',
                      padding: '4px !important',
                      margin: '0 !important',
                      width: '24px !important',
                      height: '24px !important',
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onDuplicate(rule)}
                    disabled={loading}
                    title="Duplicate rule"
                    sx={{
                      minWidth: '0 !important',
                      padding: '4px !important',
                      margin: '0 -2px 0 -2px !important',
                      width: '24px !important',
                      height: '24px !important',
                    }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => onDelete(rule.id)}
                    disabled={loading}
                    color="error"
                    title="Delete rule"
                    sx={{
                      minWidth: '0 !important',
                      padding: '4px !important',
                      margin: '0 !important',
                      width: '24px !important',
                      height: '24px !important',
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                  {onApply && (
                    <IconButton
                      size="small"
                      onClick={() => onApply(rule)}
                      disabled={
                        loading ||
                        !(rule.category_id || rule.counterparty_account_id) ||
                        (rule.pending_transaction_count ?? 0) === 0
                      }
                      title="Apply rule to existing transactions"
                      color="success"
                      sx={{
                        minWidth: '0 !important',
                        padding: '4px !important',
                        margin: '0 !important',
                        width: '24px !important',
                        height: '24px !important',
                      }}
                    >
                      <PlayArrowIcon fontSize="small" />
                    </IconButton>
                  )}
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
  )
}
