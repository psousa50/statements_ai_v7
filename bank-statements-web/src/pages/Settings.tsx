import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material'
import LightModeIcon from '@mui/icons-material/LightMode'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import SettingsBrightnessIcon from '@mui/icons-material/SettingsBrightness'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'
import './SettingsPage.css'

export const SettingsPage: React.FC = () => {
  const { user } = useAuth()
  const { mode, setMode } = useTheme()

  const handleThemeChange = (_: React.MouseEvent<HTMLElement>, newMode: string | null) => {
    if (newMode) {
      setMode(newMode as 'light' | 'dark' | 'system')
    }
  }

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user?.email?.[0].toUpperCase() || '?'

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-description">Manage your account and preferences</p>
      </div>

      <div className="settings-sections">
        <Card className="settings-card">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Profile
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Avatar src={user?.avatar_url} sx={{ width: 64, height: 64, fontSize: '1.5rem' }}>
                {initials}
              </Avatar>
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  {user?.name || 'User'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {user?.email}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card className="settings-card">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Appearance
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose how the app looks to you
            </Typography>
            <ToggleButtonGroup
              value={mode}
              exclusive
              onChange={handleThemeChange}
              aria-label="theme selection"
              className="theme-toggle-group"
            >
              <ToggleButton value="light" aria-label="light mode">
                <LightModeIcon sx={{ mr: 1 }} />
                Light
              </ToggleButton>
              <ToggleButton value="system" aria-label="system preference">
                <SettingsBrightnessIcon sx={{ mr: 1 }} />
                System
              </ToggleButton>
              <ToggleButton value="dark" aria-label="dark mode">
                <DarkModeIcon sx={{ mr: 1 }} />
                Dark
              </ToggleButton>
            </ToggleButtonGroup>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
