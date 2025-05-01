import axios from 'axios';
import {
  Transaction,
  TransactionCreate,
  TransactionListResponse,
} from '../../types/Transaction';

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || '';
const API_URL = `${BASE_URL}/api/v1/transactions`;

export const TransactionsApi = {
  /**
   * Get all transactions
   */
  getAll: async (): Promise<TransactionListResponse> => {
    const response = await axios.get<TransactionListResponse>(API_URL);
    return response.data;
  },

  /**
   * Get a transaction by ID
   */
  getById: async (id: string): Promise<Transaction> => {
    const response = await axios.get<Transaction>(`${API_URL}/${id}`);
    return response.data;
  },

  /**
   * Create a new transaction
   */
  create: async (transaction: TransactionCreate): Promise<Transaction> => {
    const response = await axios.post<Transaction>(API_URL, transaction);
    return response.data;
  },

  /**
   * Update a transaction
   */
  update: async (
    id: string,
    transaction: TransactionCreate
  ): Promise<Transaction> => {
    const response = await axios.put<Transaction>(
      `${API_URL}/${id}`,
      transaction
    );
    return response.data;
  },

  /**
   * Delete a transaction
   */
  delete: async (id: string): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`);
  },
};
