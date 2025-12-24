import React, { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Box, Typography, Button } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import { useAuth } from '../auth/AuthContext'
import './LoginPage.css'

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
    <Box className="login-page">
      <Box className="login-card">
        <Box className="login-icon">
          <AccountBalanceIcon sx={{ fontSize: 56 }} />
        </Box>
        <Typography variant="h4" component="h1" className="login-title">
          Bank Statements
        </Typography>
        <Typography variant="body1" className="login-subtitle">
          Track and categorise your transactions
        </Typography>

        <Button
          variant="contained"
          size="large"
          fullWidth
          startIcon={<GoogleIcon />}
          onClick={() => login('google')}
          className="google-button"
        >
          Continue with Google
        </Button>
      </Box>
    </Box>
  )
}
