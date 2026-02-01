import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { IconButton, Menu, MenuItem, Avatar, Typography, Box, Divider, Chip } from '@mui/material'
import SettingsIcon from '@mui/icons-material/Settings'
import LogoutIcon from '@mui/icons-material/Logout'
import { useAuth } from '../../auth/AuthContext'
import { useSubscription } from '../../services/hooks/useSubscription'

export const UserMenu: React.FC = () => {
  const { user, logout } = useAuth()
  const { subscription } = useSubscription()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    handleClose()
    await logout()
  }

  if (!user) return null

  const initials = user.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user.email[0].toUpperCase()

  return (
    <>
      <IconButton onClick={handleClick} size="small" sx={{ ml: 2 }}>
        <Avatar src={user.avatar_url} alt={user.name || user.email} sx={{ width: 32, height: 32 }}>
          {initials}
        </Avatar>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{ sx: { minWidth: 200 } }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="subtitle2" noWrap>
              {user.name || 'User'}
            </Typography>
            {subscription && (
              <Chip
                label={subscription.tier.toUpperCase()}
                size="small"
                color={subscription.tier === 'free' ? 'default' : 'warning'}
                sx={{ height: 18, fontSize: '0.65rem' }}
              />
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" noWrap>
            {user.email}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={() => navigate('/settings')}>
          <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
          Sign out
        </MenuItem>
      </Menu>
    </>
  )
}
