import React from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import BarChartIcon from '@mui/icons-material/BarChart'
import CategoryIcon from '@mui/icons-material/Category'
import AccountTreeIcon from '@mui/icons-material/AccountTree'

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
          to="/categorizations"
          selected={location.pathname === '/categorizations'}
        >
          <ListItemIcon>
            <CategoryIcon />
          </ListItemIcon>
          <ListItemText primary="Categorizations" />
        </ListItemButton>
      </ListItem>
      
      <ListItem disablePadding>
        <ListItemButton
          component={RouterLink}
          to="/categories"
          selected={location.pathname === '/categories'}
        >
          <ListItemIcon>
            <AccountTreeIcon />
          </ListItemIcon>
          <ListItemText primary="Categories" />
        </ListItemButton>
      </ListItem>
      
      <ListItem disablePadding>
        <ListItemButton
          component={RouterLink}
          to="/charts"
          selected={location.pathname === '/charts'}
        >
          <ListItemIcon>
            <BarChartIcon />
          </ListItemIcon>
          <ListItemText primary="Charts" />
        </ListItemButton>
      </ListItem>
      
      <ListItem disablePadding>
        <ListItemButton
          component={RouterLink}
          to="/upload"
          selected={location.pathname === '/upload'}
        >
          <ListItemIcon>
            <UploadFileIcon />
          </ListItemIcon>
          <ListItemText primary="Upload Statement" />
        </ListItemButton>
      </ListItem>
    </List>
  )
}
