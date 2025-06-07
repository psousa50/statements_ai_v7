import React from 'react'
import { Box, Card, CardContent, Typography, Stack, Chip } from '@mui/material'
import { StatementAnalysisResponse } from '../../api/StatementClient'

interface AnalysisSummaryProps {
  analysisData: StatementAnalysisResponse
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({ analysisData }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR', // You might want to make this configurable
    }).format(amount)
  }

  const formatDateRange = (dateRange: [string, string]) => {
    if (!dateRange[0] || !dateRange[1]) {
      return 'No valid dates'
    }
    if (dateRange[0] === dateRange[1]) {
      return dateRange[0]
    }
    return `${dateRange[0]} to ${dateRange[1]}`
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Transaction Analysis Summary
      </Typography>

      {/* All cards in one row */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: 2,
        }}
      >
        {/* File & Date Info */}
        <Card variant="outlined">
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
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2">Date Range:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {formatDateRange(analysisData.date_range)}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Transaction Counts */}
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Transaction Counts
            </Typography>
            <Stack spacing={1}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2">Total:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {analysisData.total_transactions}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2">Unique:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {analysisData.unique_transactions}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Chip
                  size="small"
                  label="Duplicates"
                  color={analysisData.duplicate_transactions > 0 ? 'warning' : 'success'}
                  variant="filled"
                />
                <Typography variant="body2" fontWeight="bold">
                  {analysisData.duplicate_transactions}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Amount Summary */}
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Amount Summary
            </Typography>
            <Stack spacing={1}>
              <Box textAlign="center">
                <Typography variant="body2" color="textSecondary">
                  Net Total
                </Typography>
                <Typography
                  variant="h6"
                  color={analysisData.total_amount >= 0 ? 'success.main' : 'error.main'}
                  fontWeight="bold"
                >
                  {formatCurrency(analysisData.total_amount)}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="success.main">
                  Credits:
                </Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  {formatCurrency(analysisData.total_credit)}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="error.main">
                  Debits:
                </Typography>
                <Typography variant="body2" fontWeight="bold" color="error.main">
                  {formatCurrency(Math.abs(analysisData.total_debit))}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Box>
  )
}
