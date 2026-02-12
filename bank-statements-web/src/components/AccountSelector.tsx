import { Account } from '../types/Transaction'
import { StyledSelect } from './StyledSelect'
import './AccountSelector.css'

interface AccountSelectorProps {
  accounts: Account[]
  selectedAccountId?: string
  onAccountChange: (accountId: string) => void
  placeholder?: string
}

export const AccountSelector = ({
  accounts,
  selectedAccountId,
  onAccountChange,
  placeholder = 'Select an account',
}: AccountSelectorProps) => {
  return (
    <div className="account-selector">
      <StyledSelect
        value={selectedAccountId || ''}
        onChange={onAccountChange}
        placeholder={placeholder}
        options={accounts.map((account) => ({
          value: account.id,
          label: account.name,
        }))}
      />
    </div>
  )
}
