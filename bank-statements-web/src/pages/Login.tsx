import React, { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Box, Paper, Typography, Button, Divider } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { useAuth } from '../auth/AuthContext'

export const Login: React.FC = () => {
  const { login, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, from])

  if (isLoading) {
    return null
  }

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
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Bank Statements
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Sign in to manage your transactions
        </Typography>

        <Divider sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Continue with
          </Typography>
        </Divider>

        <Button
          variant="outlined"
          size="large"
          fullWidth
          startIcon={<GoogleIcon />}
          onClick={() => login('google')}
          sx={{ textTransform: 'none', py: 1.5 }}
        >
          Google
        </Button>
      </Paper>
    </Box>
  )
}
