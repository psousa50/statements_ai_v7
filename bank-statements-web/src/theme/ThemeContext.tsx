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

const THEME_STORAGE_KEY = 'theme-mode'

const getStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'system'
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored
  }
  return 'system'
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemPrefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
  const [mode, setModeState] = useState<ThemeMode>(getStoredTheme)

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode)
    localStorage.setItem(THEME_STORAGE_KEY, newMode)
  }

  const resolvedMode = mode === 'system' ? (systemPrefersDarkMode ? 'dark' : 'light') : mode

  useEffect(() => {
    const root = document.documentElement
    const body = document.body

    root.setAttribute('data-theme', resolvedMode)

    if (resolvedMode === 'dark') {
      body.classList.add('rs-theme-dark')
      body.classList.remove('rs-theme-light')
    } else {
      body.classList.add('rs-theme-light')
      body.classList.remove('rs-theme-dark')
    }
  }, [resolvedMode])

  const muiTheme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: resolvedMode,
          primary: {
            main: resolvedMode === 'dark' ? '#fbbf24' : '#b45309',
          },
          background: {
            default: resolvedMode === 'dark' ? '#0f172a' : '#f8fafc',
            paper: resolvedMode === 'dark' ? '#151921' : '#ffffff',
          },
        },
        components: {
          MuiDrawer: {
            styleOverrides: {
              paper: {
                backgroundColor: resolvedMode === 'dark' ? 'rgba(15, 23, 42, 0.95)' : '#ffffff',
                backdropFilter: resolvedMode === 'dark' ? 'blur(12px)' : 'none',
                borderRight: resolvedMode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #e2e8f0',
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundColor: resolvedMode === 'dark' ? 'rgba(15, 23, 42, 0.9)' : '#ffffff',
                backdropFilter: resolvedMode === 'dark' ? 'blur(12px)' : 'none',
                borderBottom: resolvedMode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #e2e8f0',
                boxShadow: 'none',
              },
            },
          },
          MuiListItemButton: {
            styleOverrides: {
              root: {
                borderRadius: 8,
                margin: '2px 8px',
                '&.Mui-selected': {
                  backgroundColor: resolvedMode === 'dark' ? 'rgba(251, 191, 36, 0.15)' : 'rgba(251, 191, 36, 0.1)',
                  '&:hover': {
                    backgroundColor: resolvedMode === 'dark' ? 'rgba(251, 191, 36, 0.2)' : 'rgba(251, 191, 36, 0.15)',
                  },
                },
                '&:hover': {
                  backgroundColor: resolvedMode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
                },
              },
            },
          },
          MuiListItemIcon: {
            styleOverrides: {
              root: {
                color: resolvedMode === 'dark' ? '#94a3b8' : '#64748b',
                minWidth: 40,
              },
            },
          },
          MuiListItemText: {
            styleOverrides: {
              primary: {
                color: resolvedMode === 'dark' ? '#f1f5f9' : '#0f172a',
                fontSize: '0.875rem',
                fontWeight: 500,
              },
            },
          },
          MuiTableCell: {
            styleOverrides: {
              head: {
                backgroundColor: resolvedMode === 'dark' ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
                fontWeight: 600,
                fontSize: '0.6875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: resolvedMode === 'dark' ? '#cbd5e1' : '#475569',
                whiteSpace: 'nowrap',
                borderBottom: resolvedMode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #e2e8f0',
              },
            },
          },
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
