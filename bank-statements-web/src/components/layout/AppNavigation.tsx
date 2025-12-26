import React from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Box,
} from '@mui/material'
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import BarChartIcon from '@mui/icons-material/BarChart'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import DescriptionIcon from '@mui/icons-material/Description'
import RepeatIcon from '@mui/icons-material/Repeat'
import QueryStatsIcon from '@mui/icons-material/QueryStats'
import SettingsIcon from '@mui/icons-material/Settings'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'

interface AppNavigationProps {
  onNavigate?: () => void
}

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
  matchPaths?: string[]
}

interface NavSection {
  title: string
  icon: React.ReactNode
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Analyse',
    icon: <QueryStatsIcon fontSize="small" />,
    items: [
      {
        path: '/transactions',
        label: 'Transactions',
        icon: <ReceiptLongIcon />,
        matchPaths: ['/transactions', '/'],
      },
      { path: '/charts', label: 'Charts', icon: <BarChartIcon /> },
      { path: '/recurring', label: 'Recurring', icon: <RepeatIcon /> },
    ],
  },
  {
    title: 'Configure',
    icon: <SettingsIcon fontSize="small" />,
    items: [
      { path: '/categories', label: 'Categories', icon: <AccountTreeIcon /> },
      { path: '/enhancement-rules', label: 'Enhancement Rules', icon: <AutoFixHighIcon /> },
      { path: '/accounts', label: 'Accounts', icon: <AccountBalanceIcon /> },
    ],
  },
  {
    title: 'Import',
    icon: <CloudUploadIcon fontSize="small" />,
    items: [
      { path: '/upload', label: 'Upload Statement', icon: <UploadFileIcon /> },
      { path: '/statements', label: 'Statements', icon: <DescriptionIcon /> },
    ],
  },
  {
    title: 'AI',
    icon: <AutoAwesomeIcon fontSize="small" />,
    items: [],
  },
]

export const AppNavigation: React.FC<AppNavigationProps> = ({ onNavigate }) => {
  const location = useLocation()

  const isSelected = (item: NavItem) => {
    if (item.matchPaths) {
      return item.matchPaths.includes(location.pathname)
    }
    return location.pathname === item.path
  }

  return (
    <List sx={{ pt: 0 }}>
      {navSections.map((section) => (
        <React.Fragment key={section.title}>
          <ListSubheader
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              bgcolor: 'background.paper',
              lineHeight: '36px',
              mt: 1,
            }}
          >
            <Box sx={{ color: 'text.secondary', display: 'flex' }}>{section.icon}</Box>
            {section.title}
          </ListSubheader>
          {section.items.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="Coming soon..."
                primaryTypographyProps={{
                  variant: 'body2',
                  color: 'text.disabled',
                  fontStyle: 'italic',
                  sx: { pl: 1 },
                }}
              />
            </ListItem>
          ) : (
            section.items.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  component={RouterLink}
                  to={item.path}
                  selected={isSelected(item)}
                  onClick={onNavigate}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))
          )}
        </React.Fragment>
      ))}
    </List>
  )
}
