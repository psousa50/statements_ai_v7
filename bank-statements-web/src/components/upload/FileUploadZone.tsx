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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  })

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
      }}
      {...getRootProps()}
    >
      <input {...getInputProps()} />

      {isLoading ? (
        <CircularProgress />
      ) : (
        <>
          <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Drag & drop your bank statement file here
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            or
          </Typography>
          <Button variant="outlined" component="span">
            Browse Files
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Supported formats: CSV, XLSX (max 10MB)
          </Typography>

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
