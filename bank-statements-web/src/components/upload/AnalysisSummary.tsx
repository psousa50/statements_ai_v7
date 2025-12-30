import React from 'react'
import { Box, Card, CardContent, Typography, Stack, Chip, Skeleton } from '@mui/material'
import { StatementAnalysisResponse, StatisticsPreviewResponse } from '../../api/StatementClient'
import { formatCurrency } from '../../utils/format'

interface AnalysisSummaryProps {
  analysisData: StatementAnalysisResponse
  previewStats?: StatisticsPreviewResponse | null
  isLoadingPreview?: boolean
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({ analysisData, previewStats, isLoadingPreview }) => {
  const stats = previewStats || analysisData
  const isFiltered = !!previewStats

  const formatDateRange = (dateRange: [string, string]) => {
    if (!dateRange[0] || !dateRange[1]) {
      return 'No valid dates'
    }
    if (dateRange[0] === dateRange[1]) {
      return dateRange[0]
    }
    return `${dateRange[0]} to ${dateRange[1]}`
  }

  const renderValue = (value: React.ReactNode) => {
    if (isLoadingPreview) {
      return <Skeleton width={60} height={24} />
    }
    return value
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Transaction Analysis Summary
      </Typography>

      {isFiltered && <Chip size="small" label="Filtered preview" color="info" variant="outlined" sx={{ mb: 1 }} />}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: 2,
        }}
      >
        <Card variant="outlined" sx={isFiltered ? { borderColor: 'info.main' } : undefined}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              File Information
            </Typography>
            <Stack spacing={1}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2">Type:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {analysisData.file_type}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Date Range:</Typography>
                {renderValue(
                  <Typography variant="body2" fontWeight="bold">
                    {formatDateRange(stats.date_range)}
                  </Typography>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={isFiltered ? { borderColor: 'info.main' } : undefined}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Transaction Counts
            </Typography>
            <Stack spacing={1}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Total:</Typography>
                {renderValue(
                  <Typography variant="body2" fontWeight="bold">
                    {stats.total_transactions}
                  </Typography>
                )}
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Unique:</Typography>
                {renderValue(
                  <Typography variant="body2" fontWeight="bold">
                    {stats.unique_transactions}
                  </Typography>
                )}
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Chip
                  size="small"
                  label="Duplicates"
                  color={stats.duplicate_transactions > 0 ? 'warning' : 'success'}
                  variant="filled"
                />
                {renderValue(
                  <Typography variant="body2" fontWeight="bold">
                    {stats.duplicate_transactions}
                  </Typography>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={isFiltered ? { borderColor: 'info.main' } : undefined}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Amount Summary
            </Typography>
            <Stack spacing={1}>
              <Box textAlign="center">
                <Typography variant="body2" color="textSecondary">
                  Net Total
                </Typography>
                {renderValue(
                  <Typography
                    variant="h6"
                    color={stats.total_amount >= 0 ? 'success.main' : 'error.main'}
                    fontWeight="bold"
                  >
                    {formatCurrency(stats.total_amount)}
                  </Typography>
                )}
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="success.main">
                  Credits:
                </Typography>
                {renderValue(
                  <Typography variant="body2" fontWeight="bold" color="success.main">
                    {formatCurrency(stats.total_credit)}
                  </Typography>
                )}
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="error.main">
                  Debits:
                </Typography>
                {renderValue(
                  <Typography variant="body2" fontWeight="bold" color="error.main">
                    {formatCurrency(Math.abs(stats.total_debit))}
                  </Typography>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Box>
  )
}
