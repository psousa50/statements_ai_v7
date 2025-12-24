import React, { createContext, useContext, useState, useEffect, useMemo } from 'react'
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material/styles'
import { useMediaQuery } from '@mui/material'
import CssBaseline from '@mui/material/CssBaseline'

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  resolvedMode: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemPrefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
  const [mode, setMode] = useState<ThemeMode>('system')

  const resolvedMode = mode === 'system' ? (systemPrefersDarkMode ? 'dark' : 'light') : mode

  useEffect(() => {
    const root = document.documentElement
    const body = document.body

    if (resolvedMode === 'dark') {
      body.classList.add('rs-theme-dark')
      body.classList.remove('rs-theme-light')

      root.style.setProperty('--bg-primary', '#2a2a2a')
      root.style.setProperty('--bg-secondary', '#1a1a1a')
      root.style.setProperty('--bg-tertiary', '#333333')
      root.style.setProperty('--bg-accent', '#1e3a8a')
      root.style.setProperty('--text-primary', 'rgba(255, 255, 255, 0.87)')
      root.style.setProperty('--text-secondary', 'rgba(255, 255, 255, 0.8)')
      root.style.setProperty('--text-muted', 'rgba(255, 255, 255, 0.6)')
      root.style.setProperty('--text-accent', '#60a5fa')
      root.style.setProperty('--border-primary', '#404040')
      root.style.setProperty('--border-secondary', '#555555')
      root.style.setProperty('--shadow-light', 'rgba(255, 255, 255, 0.1)')
      root.style.setProperty('--button-primary', '#3b82f6')
      root.style.setProperty('--button-primary-hover', '#2563eb')
      root.style.setProperty('--button-secondary', '#4a5568')
      root.style.setProperty('--positive-amount', '#5aff83')
      root.style.setProperty('--negative-amount', '#ff8080')
      root.style.setProperty('--bg-hover', '#374151')
      root.style.setProperty('--bg-elevated', '#333333')
      root.style.setProperty('--positive-amount-bg', '#064e3b')
      root.style.setProperty('--negative-amount-bg', '#7f1d1d')
    } else {
      body.classList.add('rs-theme-light')
      body.classList.remove('rs-theme-dark')

      root.style.setProperty('--bg-primary', '#ffffff')
      root.style.setProperty('--bg-secondary', '#f8fafc')
      root.style.setProperty('--bg-tertiary', '#f9fafb')
      root.style.setProperty('--bg-accent', '#eff6ff')
      root.style.setProperty('--text-primary', '#1f2937')
      root.style.setProperty('--text-secondary', '#374151')
      root.style.setProperty('--text-muted', '#6b7280')
      root.style.setProperty('--text-accent', '#1e40af')
      root.style.setProperty('--border-primary', '#e5e7eb')
      root.style.setProperty('--border-secondary', '#d1d5db')
      root.style.setProperty('--shadow-light', 'rgba(0, 0, 0, 0.1)')
      root.style.setProperty('--button-primary', '#007bff')
      root.style.setProperty('--button-primary-hover', '#0069d9')
      root.style.setProperty('--button-secondary', '#6c757d')
      root.style.setProperty('--positive-amount', '#059669')
      root.style.setProperty('--negative-amount', '#dc2626')
      root.style.setProperty('--bg-hover', '#f3f4f6')
      root.style.setProperty('--bg-elevated', '#ffffff')
      root.style.setProperty('--positive-amount-bg', '#d1fae5')
      root.style.setProperty('--negative-amount-bg', '#fee2e2')
    }
  }, [resolvedMode])

  const muiTheme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: resolvedMode,
        },
      }),
    [resolvedMode]
  )

  return (
    <ThemeContext.Provider value={{ mode, setMode, resolvedMode }}>
      <MuiThemeProvider theme={muiTheme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  )
}

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
