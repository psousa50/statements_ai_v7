import React from 'react'
import { Box, Card, CardContent, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material'
import { SampleData } from '../../api/StatementClient'

interface AnalysisSummaryProps {
  fileType: string
  rowCount: number
  dateRange?: { start: string; end: string }
  totalAmount?: number
  sampleData: SampleData[]
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({
  fileType,
  rowCount,
  dateRange,
  totalAmount,
  sampleData,
}) => {
  const calculatedDateRange = React.useMemo(() => {
    if (dateRange) return dateRange
    
    if (sampleData.length === 0) return undefined
    
    const dates = sampleData
      .map(item => new Date(item.date))
      .filter(date => !isNaN(date.getTime()))
    
    if (dates.length === 0) return undefined
    
    const start = new Date(Math.min(...dates.map(d => d.getTime())))
    const end = new Date(Math.max(...dates.map(d => d.getTime())))
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    }
  }, [dateRange, sampleData])
  
  const calculatedTotalAmount = React.useMemo(() => {
    if (totalAmount !== undefined) return totalAmount
    
    if (sampleData.length === 0) return undefined
    
    return sampleData.reduce((sum, item) => sum + (item.amount || 0), 0)
  }, [totalAmount, sampleData])

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom>
        Analysis Summary
      </Typography>
      
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
        gap: 2, 
        mb: 3 
      }}>
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              File Type
            </Typography>
            <Typography variant="h6">{fileType}</Typography>
          </CardContent>
        </Card>
        
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Rows
            </Typography>
            <Typography variant="h6">{rowCount}</Typography>
          </CardContent>
        </Card>
        
        {calculatedDateRange && (
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Date Range
              </Typography>
              <Typography variant="h6">
                {calculatedDateRange.start} to {calculatedDateRange.end}
              </Typography>
            </CardContent>
          </Card>
        )}
        
        {calculatedTotalAmount !== undefined && (
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Amount
              </Typography>
              <Typography variant="h6">
                {calculatedTotalAmount.toLocaleString('en-US', {
                  style: 'currency',
                  currency: 'USD',
                })}
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
      
      {sampleData.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            Sample Data
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small" sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sampleData.map((row, index) => (
                  <TableRow key={index}>
                    <TableCell>{row.date}</TableCell>
                    <TableCell>{row.description}</TableCell>
                    <TableCell align="right">
                      {row.amount?.toLocaleString('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  )
}
