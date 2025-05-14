import React from 'react'
import { Box, Card, CardContent, Grid, Typography } from '@mui/material'
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
      
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                File Type
              </Typography>
              <Typography variant="h6">{fileType}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Rows
              </Typography>
              <Typography variant="h6">{rowCount}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {calculatedDateRange && (
          <Grid item xs={6} sm={3}>
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
          </Grid>
        )}
        
        {calculatedTotalAmount !== undefined && (
          <Grid item xs={6} sm={3}>
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
          </Grid>
        )}
      </Grid>
      
      {sampleData.length > 0 && (
        <Box>
          <Typography variant="subtitle1" gutterBottom>
            Sample Data Preview
          </Typography>
          <Box sx={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Date</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Description</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>Amount</th>
                  {sampleData[0]?.category && (
                    <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Category</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {sampleData.map((row, index) => (
                  <tr key={index}>
                    <td style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>{row.date}</td>
                    <td style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>{row.description}</td>
                    <td style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                      {row.amount.toLocaleString('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      })}
                    </td>
                    {row.category && (
                      <td style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>{row.category}</td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Box>
      )}
    </Box>
  )
}
