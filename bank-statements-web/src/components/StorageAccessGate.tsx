import React from 'react'
import { Box, Paper, Typography, Button, CircularProgress } from '@mui/material'
import { useStorageAccess } from '../hooks/useStorageAccess'

interface Props {
  children: React.ReactNode
}

export const StorageAccessGate: React.FC<Props> = ({ children }) => {
  const { needsPrompt, isReady, isChecking, requestAccess } = useStorageAccess()

  if (isChecking) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  if (needsPrompt && !isReady) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            maxWidth: 400,
            width: '100%',
            textAlign: 'center',
            mx: 2,
          }}
        >
          <Typography variant="h5" component="h1" gutterBottom>
            Enable Cookies
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            This app needs cookie access to keep you signed in. Tap below to continue.
          </Typography>
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={requestAccess}
            sx={{ textTransform: 'none', py: 1.5 }}
          >
            Continue
          </Button>
        </Paper>
      </Box>
    )
  }

  return <>{children}</>
}
