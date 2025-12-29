import React from 'react'
import {
  Alert,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { DroppedRow } from '../../api/StatementClient'

interface DroppedRowsWarningProps {
  droppedRows: DroppedRow[]
  onDismiss?: () => void
  onContinue?: () => void
}

export const DroppedRowsWarning: React.FC<DroppedRowsWarningProps> = ({ droppedRows, onDismiss, onContinue }) => {
  if (droppedRows.length === 0) {
    return null
  }

  const invalidDateCount = droppedRows.filter((r) => r.reason === 'invalid_date').length
  const invalidAmountCount = droppedRows.filter((r) => r.reason === 'invalid_amount').length

  const getSummaryMessage = () => {
    const parts: string[] = []
    if (invalidDateCount > 0) {
      parts.push(`${invalidDateCount} with invalid date${invalidDateCount !== 1 ? 's' : ''}`)
    }
    if (invalidAmountCount > 0) {
      parts.push(`${invalidAmountCount} with invalid amount${invalidAmountCount !== 1 ? 's' : ''}`)
    }
    return `${droppedRows.length} row${droppedRows.length !== 1 ? 's' : ''} will be skipped: ${parts.join(', ')}`
  }

  return (
    <Alert severity="warning" onClose={onDismiss} sx={{ mb: 2 }}>
      <Box>
        <Typography variant="body2" fontWeight="medium">
          {getSummaryMessage()}
        </Typography>
      </Box>

      <TableContainer sx={{ mt: 2, maxHeight: 300 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'warning.light' }}>Row</TableCell>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'warning.light' }}>Date Value</TableCell>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'warning.light' }}>Description</TableCell>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'warning.light' }}>Amount</TableCell>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'warning.light' }}>Issue</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {droppedRows.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.file_row_number}</TableCell>
                <TableCell sx={{ color: row.reason === 'invalid_date' ? 'error.main' : 'inherit' }}>
                  {row.date_value || '(empty)'}
                </TableCell>
                <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {row.description || '(empty)'}
                </TableCell>
                <TableCell sx={{ color: row.reason === 'invalid_amount' ? 'error.main' : 'inherit' }}>
                  {row.amount || '(empty)'}
                </TableCell>
                <TableCell sx={{ color: 'error.main', whiteSpace: 'nowrap' }}>
                  {row.reason === 'invalid_date' ? 'Invalid date' : 'Invalid amount'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {onContinue && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="contained" color="primary" onClick={onContinue}>
            Continue to Transactions
          </Button>
        </Box>
      )}
    </Alert>
  )
}
