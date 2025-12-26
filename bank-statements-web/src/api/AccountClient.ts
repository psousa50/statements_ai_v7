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
  getById: (id: string) => Promise<Account>
  createAccount: (name: string) => Promise<Account>
  updateAccount: (id: string, name: string) => Promise<Account>
  deleteAccount: (id: string) => Promise<void>
  setInitialBalance: (id: string, balanceDate: string, balanceAmount: number) => Promise<Account>
  deleteInitialBalance: (id: string) => Promise<void>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/accounts`

export const accountClient: AccountClient = {
  getAll: async (): Promise<Account[]> => {
    const response = await axios.get<{ accounts: Account[]; total: number }>(API_URL)
    return response.data.accounts
  },

  getById: async (id: string): Promise<Account> => {
    const response = await axios.get<Account>(`${API_URL}/${id}`)
    return response.data
  },

  createAccount: async (name: string): Promise<Account> => {
    const response = await axios.post<Account>(API_URL, { name })
    return response.data
  },

  updateAccount: async (id: string, name: string): Promise<Account> => {
    const response = await axios.put<Account>(`${API_URL}/${id}`, { name })
    return response.data
  },

  deleteAccount: async (id: string): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  setInitialBalance: async (id: string, balanceDate: string, balanceAmount: number): Promise<Account> => {
    const response = await axios.put<Account>(`${API_URL}/${id}/initial-balance`, {
      balance_date: balanceDate,
      balance_amount: balanceAmount,
    })
    return response.data
  },

  deleteInitialBalance: async (id: string): Promise<void> => {
    await axios.delete(`${API_URL}/${id}/initial-balance`)
  },
}
