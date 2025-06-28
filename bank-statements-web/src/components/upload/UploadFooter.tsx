import React from 'react'
import { Box, Button, CircularProgress } from '@mui/material'

interface UploadFooterProps {
  isValid: boolean
  isUploading: boolean
  onFinalize: () => void
  onCancel: () => void
}

export const UploadFooter: React.FC<UploadFooterProps> = ({ isValid, isUploading, onFinalize, onCancel }) => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
      <Button variant="outlined" color="secondary" onClick={onCancel} disabled={isUploading}>
        Cancel
      </Button>

      <Button
        variant="contained"
        color="primary"
        onClick={onFinalize}
        disabled={!isValid || isUploading}
        startIcon={isUploading ? <CircularProgress size={20} color="inherit" /> : null}
      >
        {isUploading ? 'Uploading...' : 'Finalize Upload'}
      </Button>
    </Box>
  )
}
