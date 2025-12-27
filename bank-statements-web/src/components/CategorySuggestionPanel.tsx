import { useState } from 'react'
import { Box, Checkbox, Chip, CircularProgress, Collapse, IconButton, Typography, Button, Alert } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import { CategorySuggestion } from '../api/CategoryClient'

interface CategorySuggestionPanelProps {
  suggestions: CategorySuggestion[]
  selectedItems: Map<string, Set<string>>
  loading: boolean
  creating: boolean
  error: string | null
  totalDescriptionsAnalysed: number
  onToggleParent: (parentName: string, suggestion: CategorySuggestion) => void
  onToggleSubcategory: (parentName: string, subcategoryName: string) => void
  onCreateSelected: () => void
  onClose: () => void
  selectedCount: { parentCount: number; subcategoryCount: number; total: number }
}

export const CategorySuggestionPanel = ({
  suggestions,
  selectedItems,
  loading,
  creating,
  error,
  totalDescriptionsAnalysed,
  onToggleParent,
  onToggleSubcategory,
  onCreateSelected,
  onClose,
  selectedCount,
}: CategorySuggestionPanelProps) => {
  const [expandedSuggestions, setExpandedSuggestions] = useState<Set<string>>(() => {
    return new Set(suggestions.map((s) => s.parent_name))
  })

  const toggleExpanded = (parentName: string) => {
    setExpandedSuggestions((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(parentName)) {
        newSet.delete(parentName)
      } else {
        newSet.add(parentName)
      }
      return newSet
    })
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, gap: 2 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Analysing transactions and generating category suggestions...
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  if (suggestions.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No category suggestions available.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Upload some transactions first to generate suggestions.
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Analysed {totalDescriptionsAnalysed} unique transaction descriptions
        </Typography>
        <Chip
          label={`${selectedCount.total} selected`}
          size="small"
          color={selectedCount.total > 0 ? 'primary' : 'default'}
        />
      </Box>

      <Box sx={{ maxHeight: '400px', overflowY: 'auto', mb: 2 }}>
        {suggestions.map((suggestion) => {
          const isParentSelected = selectedItems.has(suggestion.parent_name)
          const selectedSubs = selectedItems.get(suggestion.parent_name) || new Set()
          const isExpanded = expandedSuggestions.has(suggestion.parent_name)
          const newSubcategories = suggestion.subcategories.filter((sub) => sub.is_new)
          const allNewSubsSelected = newSubcategories.every((sub) => selectedSubs.has(sub.name))

          return (
            <Box
              key={suggestion.parent_name}
              sx={{
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                mb: 1,
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1.5,
                  backgroundColor: 'var(--bg-secondary)',
                  cursor: 'pointer',
                  '&:hover': { backgroundColor: 'var(--bg-hover)' },
                }}
                onClick={() => toggleExpanded(suggestion.parent_name)}
              >
                <IconButton size="small" sx={{ mr: 1 }}>
                  {isExpanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
                </IconButton>

                <Checkbox
                  checked={isParentSelected && (suggestion.parent_is_new || allNewSubsSelected)}
                  indeterminate={isParentSelected && !allNewSubsSelected && selectedSubs.size > 0}
                  disabled={!suggestion.parent_is_new && newSubcategories.length === 0}
                  onClick={(e) => {
                    e.stopPropagation()
                    onToggleParent(suggestion.parent_name, suggestion)
                  }}
                  size="small"
                />

                <Box sx={{ flex: 1, ml: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2">{suggestion.parent_name}</Typography>
                    {!suggestion.parent_is_new && (
                      <Chip
                        label="Exists"
                        size="small"
                        variant="outlined"
                        icon={<CheckCircleOutlineIcon sx={{ fontSize: '14px !important' }} />}
                        sx={{ height: '20px', fontSize: '11px' }}
                      />
                    )}
                    <Chip
                      label={`${Math.round(suggestion.confidence * 100)}%`}
                      size="small"
                      color={
                        suggestion.confidence >= 0.8 ? 'success' : suggestion.confidence >= 0.5 ? 'warning' : 'default'
                      }
                      sx={{ height: '20px', fontSize: '11px' }}
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {suggestion.subcategories.length} subcategories
                  </Typography>
                </Box>
              </Box>

              <Collapse in={isExpanded}>
                <Box sx={{ pl: 6, pr: 2, pb: 1.5 }}>
                  {suggestion.subcategories.map((sub) => (
                    <Box
                      key={sub.name}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        py: 0.5,
                        opacity: sub.is_new ? 1 : 0.6,
                      }}
                    >
                      <Checkbox
                        checked={selectedSubs.has(sub.name)}
                        disabled={!sub.is_new}
                        onChange={() => onToggleSubcategory(suggestion.parent_name, sub.name)}
                        size="small"
                      />
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {sub.name}
                      </Typography>
                      {!sub.is_new && (
                        <Chip
                          label="Exists"
                          size="small"
                          variant="outlined"
                          sx={{ ml: 1, height: '18px', fontSize: '10px' }}
                        />
                      )}
                    </Box>
                  ))}

                  {suggestion.matched_descriptions.length > 0 && (
                    <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid var(--border-color)' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        Matched transactions:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {suggestion.matched_descriptions.slice(0, 5).map((desc, i) => (
                          <Chip
                            key={i}
                            label={desc.length > 30 ? `${desc.substring(0, 30)}...` : desc}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        ))}
                        {suggestion.matched_descriptions.length > 5 && (
                          <Chip
                            label={`+${suggestion.matched_descriptions.length - 5} more`}
                            size="small"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        )}
                      </Box>
                    </Box>
                  )}
                </Box>
              </Collapse>
            </Box>
          )
        })}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="outlined" onClick={onClose} disabled={creating}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={onCreateSelected}
          disabled={creating || selectedCount.total === 0}
          startIcon={creating ? <CircularProgress size={16} /> : undefined}
        >
          {creating ? 'Creating...' : `Create ${selectedCount.total} Categories`}
        </Button>
      </Box>
    </Box>
  )
}
