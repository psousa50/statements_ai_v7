import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Box, Button, CircularProgress, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'

interface FileUploadZoneProps {
  onFileSelected: (file: File) => void
  isLoading: boolean
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({ onFileSelected, isLoading }) => {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null)
      if (acceptedFiles.length === 0) {
        return
      }

      const file = acceptedFiles[0]
      
      // Check file type
      if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
        setError('Only CSV and XLSX files are supported')
        return
      }
      
      // Check file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB')
        return
      }
      
      onFileSelected(file)
    },
    [onFileSelected]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <Box
      sx={{
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.400',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        backgroundColor: isDragActive ? 'rgba(0, 0, 0, 0.05)' : 'transparent',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        mb: 3,
      }}
      {...getRootProps()}
    >
      <input {...getInputProps()} />
      
      {isLoading ? (
        <Box display="flex" flexDirection="column" alignItems="center">
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography>Analyzing your statement...</Typography>
        </Box>
      ) : (
        <>
          <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop your file here' : 'Drag and drop your bank statement'}
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Supported formats: CSV, XLSX (Max 10MB)
          </Typography>
          <Button variant="contained" color="primary" sx={{ mt: 2 }}>
            Browse Files
          </Button>
          
          {error && (
            <Typography color="error" sx={{ mt: 2 }}>
              {error}
            </Typography>
          )}
        </>
      )}
    </Box>
  )
}
