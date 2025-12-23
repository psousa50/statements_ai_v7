import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Box, CircularProgress, Typography, Alert } from '@mui/material'
import { useAuth } from '../auth/AuthContext'
import { authClient } from '../api/AuthClient'

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { refreshUser } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      const errorParam = searchParams.get('error')
      if (errorParam) {
        setError(errorParam)
        return
      }

      const code = searchParams.get('code')
      if (code) {
        try {
          // Exchange the auth code for session cookies
          await authClient.exchangeAuthCode(code)
        } catch (err) {
          setError('Failed to complete authentication. Please try again.')
          return
        }
      }

      try {
        await refreshUser()
        navigate('/', { replace: true })
      } catch (err) {
        setError('Authentication failed. Please try again.')
      }
    }

    handleCallback()
  }, [searchParams, refreshUser, navigate])

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
        </Alert>
        <Typography
          variant="body2"
          sx={{ cursor: 'pointer', textDecoration: 'underline' }}
          onClick={() => navigate('/login')}
        >
          Return to login
        </Typography>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
      }}
    >
      <CircularProgress />
      <Typography variant="body1" color="text.secondary">
        Completing sign in...
      </Typography>
    </Box>
  )
}
