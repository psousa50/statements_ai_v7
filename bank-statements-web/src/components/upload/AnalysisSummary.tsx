import React from 'react'
import { Box, Card, CardContent, Typography } from '@mui/material'
import { SampleData } from '../../api/StatementClient'

interface AnalysisSummaryProps {
  fileType: string
  rowCount?: number
  dateRange?: { start: string; end: string }
  totalAmount?: number
  sampleData: SampleData
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({
  fileType,
  rowCount,
  dateRange,
  totalAmount,
  sampleData,
}) => {
  // Calculate the actual row count from the sample data if not provided
  const actualRowCount = rowCount || (sampleData.rows ? sampleData.rows.length : 0)

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
            <Typography variant="h6">{sampleData.metadata.header_row_index + 1}</Typography>
          </CardContent>
        </Card>
        
        <Card variant="outlined">
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Data Start Row
            </Typography>
            <Typography variant="h6">{sampleData.metadata.data_start_row_index + 1}</Typography>
          </CardContent>
        </Card>
      </Box>
      

    </Box>
  )
}
