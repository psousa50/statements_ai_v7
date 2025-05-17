import React from 'react'
import { Box, Card, CardContent, Typography } from '@mui/material'
import { SampleData } from '../../api/StatementClient'

interface AnalysisSummaryProps {
  fileType: string
  rowCount?: number
  dateRange?: { start: string; end: string }
  totalAmount?: number
  sampleData: string[][]
  headerRowIndex?: number
  dataStartRowIndex?: number
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({
  fileType,
  rowCount,
  dateRange,
  totalAmount,
  sampleData,
  headerRowIndex = 0,
  dataStartRowIndex = 1,
}) => {
  // Calculate the actual row count from the sample data if not provided
  const actualRowCount = rowCount || (sampleData ? sampleData.length : 0)

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
            <Typography variant="h6">{actualRowCount}</Typography>
          </CardContent>
        </Card>
        
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Header Row
            </Typography>
            <Typography variant="h6">{headerRowIndex + 1}</Typography>
          </CardContent>
        </Card>
        
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Data Start Row
            </Typography>
            <Typography variant="h6">{dataStartRowIndex + 1}</Typography>
          </CardContent>
        </Card>
      </Box>
      

    </Box>
  )
}
