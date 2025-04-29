import { useState, useEffect, useCallback } from 'react';
import { Transaction, TransactionCreate } from '../../types/Transaction';
import { TransactionsApi } from '../api/transactions';

export const useTransactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await TransactionsApi.getAll();
      setTransactions(response.transactions);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError('Failed to fetch transactions. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, []);

  const addTransaction = useCallback(async (transaction: TransactionCreate) => {
    setLoading(true);
    setError(null);
    try {
      const newTransaction = await TransactionsApi.create(transaction);
      setTransactions((prev) => [...prev, newTransaction]);
      return newTransaction;
    } catch (err) {
      console.error('Error adding transaction:', err);
      setError('Failed to add transaction. Please try again later.');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  return {
    transactions,
    loading,
    error,
    fetchTransactions,
    addTransaction,
  };
};
