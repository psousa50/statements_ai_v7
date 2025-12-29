import React from 'react'
import { Alert, Box, Typography, Button } from '@mui/material'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'

interface AnalysisErrorPanelProps {
  errorMessage: string
  fileName?: string
  onDismiss: () => void
}

export const AnalysisErrorPanel: React.FC<AnalysisErrorPanelProps> = ({ errorMessage, fileName, onDismiss }) => {
  return (
    <Alert
      severity="error"
      icon={<ErrorOutlineIcon />}
      sx={{ mb: 2 }}
      action={
        <Button color="inherit" size="small" onClick={onDismiss}>
          Try Another File
        </Button>
      }
    >
      <Box>
        <Typography variant="body2" fontWeight="medium" gutterBottom>
          Failed to analyse {fileName ? `"${fileName}"` : 'file'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
          {errorMessage}
        </Typography>
      </Box>
    </Alert>
  )
}
