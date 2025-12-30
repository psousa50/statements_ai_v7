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

      root.style.setProperty('--bg-primary', '#0f172a')
      root.style.setProperty('--bg-secondary', '#1e293b')
      root.style.setProperty('--bg-tertiary', '#334155')
      root.style.setProperty('--bg-accent', 'rgba(59, 130, 246, 0.15)')
      root.style.setProperty('--bg-hover', 'rgba(255, 255, 255, 0.05)')
      root.style.setProperty('--bg-elevated', 'rgba(30, 41, 59, 0.8)')

      root.style.setProperty('--glass-bg', 'rgba(30, 41, 59, 0.6)')
      root.style.setProperty('--glass-bg-light', 'rgba(51, 65, 85, 0.4)')
      root.style.setProperty('--glass-border', 'rgba(255, 255, 255, 0.1)')
      root.style.setProperty('--glass-shadow', '0 8px 32px rgba(0, 0, 0, 0.3)')

      root.style.setProperty('--text-primary', '#f1f5f9')
      root.style.setProperty('--text-secondary', '#cbd5e1')
      root.style.setProperty('--text-muted', '#94a3b8')
      root.style.setProperty('--text-accent', '#60a5fa')

      root.style.setProperty('--border-primary', 'rgba(255, 255, 255, 0.08)')
      root.style.setProperty('--border-secondary', 'rgba(255, 255, 255, 0.12)')

      root.style.setProperty('--button-primary', '#3b82f6')
      root.style.setProperty('--button-primary-hover', '#60a5fa')
      root.style.setProperty('--button-secondary', '#64748b')

      root.style.setProperty('--positive-amount', '#34d399')
      root.style.setProperty('--negative-amount', '#f87171')
      root.style.setProperty('--positive-amount-bg', 'rgba(16, 185, 129, 0.15)')
      root.style.setProperty('--negative-amount-bg', 'rgba(239, 68, 68, 0.15)')
    } else {
      body.classList.add('rs-theme-light')
      body.classList.remove('rs-theme-dark')

      root.style.setProperty('--bg-primary', '#ffffff')
      root.style.setProperty('--bg-secondary', '#f8fafc')
      root.style.setProperty('--bg-tertiary', '#f1f5f9')
      root.style.setProperty('--bg-accent', '#eff6ff')
      root.style.setProperty('--bg-hover', '#f9fafb')
      root.style.setProperty('--bg-elevated', '#ffffff')

      root.style.setProperty('--glass-bg', '#ffffff')
      root.style.setProperty('--glass-bg-light', '#f1f5f9')
      root.style.setProperty('--glass-border', '#e2e8f0')
      root.style.setProperty('--glass-shadow', '0 4px 6px -1px rgba(0, 0, 0, 0.1)')

      root.style.setProperty('--text-primary', '#0f172a')
      root.style.setProperty('--text-secondary', '#475569')
      root.style.setProperty('--text-muted', '#64748b')
      root.style.setProperty('--text-accent', '#2563eb')

      root.style.setProperty('--border-primary', '#e2e8f0')
      root.style.setProperty('--border-secondary', '#cbd5e1')

      root.style.setProperty('--button-primary', '#3b82f6')
      root.style.setProperty('--button-primary-hover', '#2563eb')
      root.style.setProperty('--button-secondary', '#64748b')

      root.style.setProperty('--positive-amount', '#059669')
      root.style.setProperty('--negative-amount', '#dc2626')
      root.style.setProperty('--positive-amount-bg', '#d1fae5')
      root.style.setProperty('--negative-amount-bg', '#fee2e2')
    }
  }, [resolvedMode])

  const muiTheme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: resolvedMode,
          primary: {
            main: '#3b82f6',
          },
          background: {
            default: resolvedMode === 'dark' ? '#0f172a' : '#f8fafc',
            paper: resolvedMode === 'dark' ? '#1e293b' : '#ffffff',
          },
        },
        components: {
          MuiDrawer: {
            styleOverrides: {
              paper: {
                backgroundColor: resolvedMode === 'dark' ? 'rgba(15, 23, 42, 0.95)' : '#ffffff',
                backdropFilter: resolvedMode === 'dark' ? 'blur(12px)' : 'none',
                borderRight:
                  resolvedMode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #e2e8f0',
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundColor: resolvedMode === 'dark' ? 'rgba(15, 23, 42, 0.9)' : '#ffffff',
                backdropFilter: resolvedMode === 'dark' ? 'blur(12px)' : 'none',
                borderBottom:
                  resolvedMode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #e2e8f0',
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
                  backgroundColor:
                    resolvedMode === 'dark' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(59, 130, 246, 0.1)',
                  '&:hover': {
                    backgroundColor:
                      resolvedMode === 'dark' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.15)',
                  },
                },
                '&:hover': {
                  backgroundColor:
                    resolvedMode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
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
