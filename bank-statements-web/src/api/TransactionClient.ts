import { Transaction, TransactionCreate, TransactionListResponse } from '../types/Transaction'

export interface TransactionClient {
  getAll(): Promise<TransactionListResponse>
  getById(id: string): Promise<Transaction>
  create(transaction: TransactionCreate): Promise<Transaction>
  update(id: string, transaction: TransactionCreate): Promise<Transaction>
  delete(id: string): Promise<void>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/transactions`

import axios from 'axios'

export const transactionClient: TransactionClient = {
  async getAll() {
    const response = await axios.get<TransactionListResponse>(API_URL)
    return response.data
  },

  async getById(id: string) {
    const response = await axios.get<Transaction>(`${API_URL}/${id}`)
    return response.data
  },

  async create(transaction: TransactionCreate) {
    const response = await axios.post<Transaction>(API_URL, transaction)
    return response.data
  },

  async update(id: string, transaction: TransactionCreate) {
    const response = await axios.put<Transaction>(`${API_URL}/${id}`, transaction)
    return response.data
  },

  async delete(id: string) {
    await axios.delete(`${API_URL}/${id}`)
  },
}
