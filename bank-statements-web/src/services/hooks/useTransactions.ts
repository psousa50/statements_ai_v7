import { useState, useEffect, useCallback } from 'react';
import { Transaction, TransactionCreate } from '../../types/Transaction';
import { useApiClients } from '../../api/ApiClientsContext';

export const useTransactions = () => {
  const { transactionClient } = useApiClients();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await transactionClient.getAll();
      setTransactions(response.transactions);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError('Failed to fetch transactions. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [transactionClient]);

  const addTransaction = useCallback(
    async (transaction: TransactionCreate) => {
      setLoading(true);
      setError(null);
      try {
        const newTransaction = await transactionClient.create(transaction);
        setTransactions((prev) => [...prev, newTransaction]);
        return newTransaction;
      } catch (err) {
        console.error('Error adding transaction:', err);
        setError('Failed to add transaction. Please try again later.');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [transactionClient]
  );

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
