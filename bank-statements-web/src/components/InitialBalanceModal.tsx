import { useState, useEffect } from 'react'
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Stack, IconButton } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { Account } from '../types/Transaction'

interface InitialBalanceModalProps {
  open: boolean
  account: Account | null
  onSave: (accountId: string, balanceDate: string, balanceAmount: number) => Promise<unknown>
  onDelete: (accountId: string) => Promise<boolean>
  onClose: () => void
}

const formatDateForInput = (dateString?: string): string => {
  if (!dateString) {
    return new Date().toISOString().split('T')[0]
  }
  return dateString
}

export const InitialBalanceModal = ({ open, account, onSave, onDelete, onClose }: InitialBalanceModalProps) => {
  const [balanceDate, setBalanceDate] = useState('')
  const [balanceAmount, setBalanceAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const hasExistingBalance = !!account?.initial_balance

  useEffect(() => {
    if (open && account) {
      if (account.initial_balance) {
        setBalanceDate(formatDateForInput(account.initial_balance.balance_date))
        setBalanceAmount(account.initial_balance.balance_amount.toString())
      } else {
        setBalanceDate(formatDateForInput())
        setBalanceAmount('')
      }
    }
  }, [open, account])

  const handleSave = async () => {
    if (!account || !balanceDate || !balanceAmount) return

    const amount = parseFloat(balanceAmount)
    if (isNaN(amount)) return

    setSaving(true)
    try {
      await onSave(account.id, balanceDate, amount)
      onClose()
    } catch (error) {
      console.error('Failed to save initial balance:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!account) return

    setDeleting(true)
    try {
      const success = await onDelete(account.id)
      if (success) {
        onClose()
      }
    } catch (error) {
      console.error('Failed to delete initial balance:', error)
    } finally {
      setDeleting(false)
    }
  }

  const isValid = balanceDate && balanceAmount && !isNaN(parseFloat(balanceAmount))
  const isProcessing = saving || deleting

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        Initial Balance: {account?.name}
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Balance Date"
            type="date"
            value={balanceDate}
            onChange={(e) => setBalanceDate(e.target.value)}
            disabled={isProcessing}
            fullWidth
            slotProps={{
              inputLabel: { shrink: true },
            }}
            helperText="The date when this balance was valid"
          />

          <TextField
            label="Balance Amount"
            type="number"
            value={balanceAmount}
            onChange={(e) => setBalanceAmount(e.target.value)}
            disabled={isProcessing}
            fullWidth
            slotProps={{
              htmlInput: { step: '0.01' },
            }}
            helperText="The account balance as of the specified date"
            autoFocus
          />
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2, justifyContent: 'space-between' }}>
        <div>
          {hasExistingBalance && (
            <Button onClick={handleDelete} color="error" disabled={isProcessing}>
              {deleting ? 'Removing...' : 'Remove Balance'}
            </Button>
          )}
        </div>
        <Stack direction="row" spacing={1}>
          <Button onClick={onClose} disabled={isProcessing}>
            Cancel
          </Button>
          <Button onClick={handleSave} variant="contained" disabled={!isValid || isProcessing}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  )
}
