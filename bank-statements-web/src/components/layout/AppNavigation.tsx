import React from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import BarChartIcon from '@mui/icons-material/BarChart'
import CategoryIcon from '@mui/icons-material/Category'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import DescriptionIcon from '@mui/icons-material/Description'
import RepeatIcon from '@mui/icons-material/Repeat'

export const AppNavigation: React.FC = () => {
  const location = useLocation()

  return (
    <List>
      <ListItem disablePadding>
        <ListItemButton
          component={RouterLink}
          to="/transactions"
          selected={location.pathname === '/transactions' || location.pathname === '/'}
        >
          <ListItemIcon>
            <DashboardIcon />
          </ListItemIcon>
          <ListItemText primary="Transactions" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton
          component={RouterLink}
          to="/enhancement-rules"
          selected={location.pathname === '/enhancement-rules'}
        >
          <ListItemIcon>
            <CategoryIcon />
          </ListItemIcon>
          <ListItemText primary="Enhancement Rules" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/categories" selected={location.pathname === '/categories'}>
          <ListItemIcon>
            <AccountTreeIcon />
          </ListItemIcon>
          <ListItemText primary="Categories" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/accounts" selected={location.pathname === '/accounts'}>
          <ListItemIcon>
            <AccountBalanceIcon />
          </ListItemIcon>
          <ListItemText primary="Accounts" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/charts" selected={location.pathname === '/charts'}>
          <ListItemIcon>
            <BarChartIcon />
          </ListItemIcon>
          <ListItemText primary="Charts" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/recurring" selected={location.pathname === '/recurring'}>
          <ListItemIcon>
            <RepeatIcon />
          </ListItemIcon>
          <ListItemText primary="Recurring" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/statements" selected={location.pathname === '/statements'}>
          <ListItemIcon>
            <DescriptionIcon />
          </ListItemIcon>
          <ListItemText primary="Statements" />
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding>
        <ListItemButton component={RouterLink} to="/upload" selected={location.pathname === '/upload'}>
          <ListItemIcon>
            <UploadFileIcon />
          </ListItemIcon>
          <ListItemText primary="Upload Statement" />
        </ListItemButton>
      </ListItem>
    </List>
  )
}
