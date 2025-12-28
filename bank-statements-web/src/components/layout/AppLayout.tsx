import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import {
  Box,
  CssBaseline,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  Divider,
  IconButton,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import CloseIcon from '@mui/icons-material/Close'
import { AppNavigation } from './AppNavigation'
import { UserMenu } from './UserMenu'

const drawerWidth = 240

// Detect touch device - iPads and tablets should use toggleable drawer
const isTouchDevice = () => {
  if (typeof window === 'undefined') return false
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

export const AppLayout = () => {
  const theme = useTheme()
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    setIsTouch(isTouchDevice())
  }, [])

  // On touch devices (iPad), always use temporary drawer regardless of screen size
  const usePermanentDrawer = isLargeScreen && !isTouch

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const drawerContent = (
    <>
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Typography variant="h6" noWrap component="div">
          Menu
        </Typography>
        {!usePermanentDrawer && (
          <IconButton
            onClick={handleDrawerToggle}
            size="small"
            aria-label="close menu"
          >
            <CloseIcon />
          </IconButton>
        )}
      </Toolbar>
      <Divider />
      <AppNavigation onNavigate={() => !usePermanentDrawer && setMobileOpen(false)} />
    </>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          left: usePermanentDrawer ? drawerWidth : 0,
          width: usePermanentDrawer ? `calc(100% - ${drawerWidth}px)` : '100%',
        }}
      >
        <Toolbar>
          {!usePermanentDrawer && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Box sx={{ flexGrow: 1 }} />
          <UserMenu />
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: usePermanentDrawer ? drawerWidth : 0, flexShrink: 0 }}
      >
        {usePermanentDrawer ? (
          <Drawer
            variant="permanent"
            sx={{
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
            open
          >
            {drawerContent}
          </Drawer>
        ) : (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
          >
            {drawerContent}
          </Drawer>
        )}
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: { xs: 2, sm: 3 },
          mt: 8,
          maxWidth: '1600px',
          mx: 'auto',
          width: '100%',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
