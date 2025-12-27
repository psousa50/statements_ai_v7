import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import axios, { AxiosError } from 'axios'
import { AuthState } from '../types/Auth'
import { authClient, RegisterRequest, LoginRequest } from '../api/AuthClient'

interface AuthContextValue extends AuthState {
  login: (provider: 'google' | 'github') => void
  loginWithPassword: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

const TOKEN_REFRESH_INTERVAL = 14 * 60 * 1000

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  })

  const refreshIntervalRef = useRef<number | null>(null)

  const clearRefreshInterval = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }
  }, [])

  const startRefreshInterval = useCallback(() => {
    clearRefreshInterval()
    refreshIntervalRef.current = window.setInterval(async () => {
      try {
        await authClient.refreshToken()
      } catch {
        setState({ user: null, isLoading: false, isAuthenticated: false })
        clearRefreshInterval()
      }
    }, TOKEN_REFRESH_INTERVAL)
  }, [clearRefreshInterval])

  const fetchUser = useCallback(async () => {
    try {
      const user = await authClient.getCurrentUser()
      setState({ user, isLoading: false, isAuthenticated: true })
      startRefreshInterval()
    } catch (error) {
      const axiosError = error as AxiosError
      if (axiosError.response?.status === 401) {
        try {
          await authClient.refreshToken()
          const user = await authClient.getCurrentUser()
          setState({ user, isLoading: false, isAuthenticated: true })
          startRefreshInterval()
          return
        } catch {
          // Refresh failed, user is not authenticated
        }
      }
      setState({ user: null, isLoading: false, isAuthenticated: false })
      clearRefreshInterval()
    }
  }, [startRefreshInterval, clearRefreshInterval])

  useEffect(() => {
    fetchUser()
    return () => clearRefreshInterval()
  }, [fetchUser, clearRefreshInterval])

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config
        if (error.response?.status === 401 && originalRequest && !originalRequest.url?.includes('/auth/')) {
          try {
            await authClient.refreshToken()
            return axios(originalRequest)
          } catch {
            setState({ user: null, isLoading: false, isAuthenticated: false })
            clearRefreshInterval()
          }
        }
        return Promise.reject(error)
      }
    )
    return () => axios.interceptors.response.eject(interceptor)
  }, [clearRefreshInterval])

  const login = useCallback((provider: 'google' | 'github') => {
    const url = provider === 'google' ? authClient.getGoogleAuthUrl() : authClient.getGithubAuthUrl()
    window.location.href = url
  }, [])

  const logout = useCallback(async () => {
    try {
      await authClient.logout()
    } catch {
      // Ignore logout errors
    }
    setState({ user: null, isLoading: false, isAuthenticated: false })
    clearRefreshInterval()
  }, [clearRefreshInterval])

  const refreshUser = useCallback(async () => {
    await fetchUser()
  }, [fetchUser])

  const loginWithPassword = useCallback(
    async (data: LoginRequest) => {
      const user = await authClient.login(data)
      setState({ user, isLoading: false, isAuthenticated: true })
      startRefreshInterval()
    },
    [startRefreshInterval]
  )

  const register = useCallback(
    async (data: RegisterRequest) => {
      const user = await authClient.register(data)
      setState({ user, isLoading: false, isAuthenticated: true })
      startRefreshInterval()
    },
    [startRefreshInterval]
  )

  return (
    <AuthContext.Provider value={{ ...state, login, loginWithPassword, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
