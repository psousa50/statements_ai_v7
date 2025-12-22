import React from 'react'
import ReactDOM from 'react-dom/client'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { useMediaQuery } from '@mui/material'
import CssBaseline from '@mui/material/CssBaseline'
import { AuthProvider } from './auth/AuthContext'
import App from './App'
import './index.css'

const ThemedApp = () => {
  const systemPrefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
  const [manualTheme, setManualTheme] = React.useState<'system' | 'light' | 'dark'>('system')

  const prefersDarkMode = manualTheme === 'system' ? systemPrefersDarkMode : manualTheme === 'dark'

  // Update CSS variables when theme changes
  React.useEffect(() => {
    const root = document.documentElement
    const body = document.body

    if (prefersDarkMode) {
      // Add RSuite dark theme class
      body.classList.add('rs-theme-dark')
      body.classList.remove('rs-theme-light')

      // Dark theme variables
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
      // Add RSuite light theme class
      body.classList.add('rs-theme-light')
      body.classList.remove('rs-theme-dark')

      // Light theme variables
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
  }, [prefersDarkMode])

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? 'dark' : 'light',
          // Let Material-UI handle the colors automatically
        },
      }),
    [prefersDarkMode]
  )

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Theme toggle for testing */}
      <div
        style={{
          position: 'fixed',
          top: 10,
          right: 10,
          zIndex: 9999,
          display: 'flex',
          gap: '5px',
        }}
      >
        <button
          onClick={() => setManualTheme('light')}
          style={{
            padding: '5px 10px',
            fontSize: '12px',
            background: manualTheme === 'light' ? '#007bff' : 'transparent',
            color: manualTheme === 'light' ? 'white' : 'inherit',
            border: '1px solid #007bff',
          }}
        >
          Light
        </button>
        <button
          onClick={() => setManualTheme('dark')}
          style={{
            padding: '5px 10px',
            fontSize: '12px',
            background: manualTheme === 'dark' ? '#007bff' : 'transparent',
            color: manualTheme === 'dark' ? 'white' : 'inherit',
            border: '1px solid #007bff',
          }}
        >
          Dark
        </button>
        <button
          onClick={() => setManualTheme('system')}
          style={{
            padding: '5px 10px',
            fontSize: '12px',
            background: manualTheme === 'system' ? '#007bff' : 'transparent',
            color: manualTheme === 'system' ? 'white' : 'inherit',
            border: '1px solid #007bff',
          }}
        >
          System
        </button>
      </div>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ThemedApp />
  </React.StrictMode>
)
