import { Account } from '../types/Transaction'
import './AccountSelector.css'

interface AccountSelectorProps {
  accounts: Account[]
  selectedAccountId?: string
  onAccountChange: (accountId: string) => void
  placeholder?: string
  required?: boolean
}

export const AccountSelector = ({
  accounts,
  selectedAccountId,
  onAccountChange,
  placeholder = 'Select an account',
  required = false,
}: AccountSelectorProps) => {
  return (
    <div className="account-selector">
      <select
        className="account-selector-dropdown"
        value={selectedAccountId || ''}
        onChange={(e) => onAccountChange(e.target.value)}
        required={required}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name}
          </option>
        ))}
      </select>
    </div>
  )
}
