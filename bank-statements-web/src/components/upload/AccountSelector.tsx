import React, { useState, useEffect, useRef } from 'react'
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  CircularProgress,
} from '@mui/material'
import { defaultApiClient } from '../../api/createApiClient'
import { Account } from '../../api/AccountClient'

interface AccountSelectorProps {
  value: string
  onChange: (value: string) => void
}

export const AccountSelector: React.FC<AccountSelectorProps> = ({ value, onChange }) => {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [newAccountName, setNewAccountName] = useState('')
  const [creatingAccount, setCreatingAccount] = useState(false)
  const accountNameInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        setLoading(true)
        const accounts = await defaultApiClient.accounts.getAll()
        setAccounts(accounts)

        // If we have accounts and no value is selected, select the first one
        if (accounts.length > 0 && !value) {
          onChange(accounts[0].id)
        }
      } catch (error) {
        console.error('Error fetching accounts:', error)
        setError('Failed to load accounts. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchAccounts()
  }, [value, onChange])

  const handleOpenDialog = () => {
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setNewAccountName('')
  }

  const handleCreateAccount = async () => {
    if (!newAccountName.trim()) return

    try {
      setCreatingAccount(true)
      const newAccount = await defaultApiClient.accounts.createAccount(newAccountName.trim())
      setAccounts((prevAccounts) => [...prevAccounts, newAccount])
      onChange(newAccount.id)
      handleCloseDialog()
    } catch (error) {
      console.error('Error creating account:', error)
      setError('Failed to create account. Please try again.')
    } finally {
      setCreatingAccount(false)
    }
  }

  if (loading) {
    return <CircularProgress size={24} />
  }

  if (error) {
    return <Typography color="error">{error}</Typography>
  }

  return (
    <Box sx={{ mb: 2 }}>
      <FormControl sx={{ width: '100%', mb: 2 }}>
        <InputLabel id="account-select-label">Account Bank</InputLabel>
        <Select
          labelId="account-select-label"
          id="account-select"
          value={value}
          label="Account Bank"
          onChange={(e) => onChange(e.target.value)}
        >
          {accounts.map((account) => (
            <MenuItem key={account.id} value={account.id}>
              {account.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button variant="outlined" size="medium" onClick={handleOpenDialog} sx={{ width: '100%' }}>
        Add New Account
      </Button>

      <Dialog
        open={openDialog}
        onClose={handleCloseDialog}
        TransitionProps={{
          onEntered: () => accountNameInputRef.current?.focus(),
        }}
      >
        <DialogTitle>Add New Account</DialogTitle>
        <DialogContent>
          <TextField
            inputRef={accountNameInputRef}
            margin="dense"
            id="name"
            label="Account Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newAccountName}
            onChange={(e) => setNewAccountName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleCreateAccount}
            disabled={!newAccountName.trim() || creatingAccount}
            variant="contained"
          >
            {creatingAccount ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
