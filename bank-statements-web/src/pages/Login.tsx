import React, { useEffect, useState, FormEvent } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { Box, Typography, Button, TextField, Divider, Alert } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import { useAuth } from '../auth/AuthContext'
import { AxiosError } from 'axios'
import './LoginPage.css'

export const Login: React.FC = () => {
  const { login, loginWithPassword, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, from])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await loginWithPassword({ email, password })
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Login failed')
    } finally {
      setIsSubmitting(false)
    }
  }

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

        {error && (
          <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
            margin="normal"
            autoComplete="email"
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            margin="normal"
            autoComplete="current-password"
          />
          <Button type="submit" variant="contained" size="large" fullWidth disabled={isSubmitting} sx={{ mt: 2 }}>
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </Box>

        <Typography variant="body2" sx={{ mt: 2 }}>
          Don't have an account? <Link to="/register">Register</Link>
        </Typography>

        <Divider sx={{ width: '100%', my: 3 }}>or</Divider>

        <Button
          variant="outlined"
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
