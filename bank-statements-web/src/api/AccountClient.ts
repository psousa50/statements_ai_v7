import axios from 'axios'
import { Account } from '../types/Transaction'

// Re-export Account type for convenience
export type { Account }

export interface AccountListResponse {
  accounts: Account[]
  total: number
}

export interface AccountClient {
  getAll: () => Promise<Account[]>
  createAccount: (name: string) => Promise<Account>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/accounts`

export const accountClient: AccountClient = {
  getAll: async (): Promise<Account[]> => {
    const response = await axios.get<{ accounts: Account[]; total: number }>(API_URL)
    return response.data.accounts
  },

  createAccount: async (name: string): Promise<Account> => {
    const response = await axios.post<Account>(API_URL, { name })
    return response.data
  },
}
