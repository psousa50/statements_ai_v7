import { useState } from 'react';
import { useTransactions } from '../services/hooks/useTransactions';
import { useCategories } from '../services/hooks/useCategories';
import { TransactionForm } from '../components/TransactionForm';
import { TransactionTable } from '../components/TransactionTable';
import { TransactionCreate } from '../types/Transaction';

export const TransactionsPage = () => {
  const {
    transactions,
    loading: transactionsLoading,
    error: transactionsError,
    addTransaction,
    categorizeTransaction,
  } = useTransactions();

  const {
    categories,
    loading: categoriesLoading,
    error: categoriesError,
  } = useCategories();

  const loading = transactionsLoading || categoriesLoading;
  const error = transactionsError || categoriesError;

  const handleAddTransaction = async (transaction: TransactionCreate) => {
    await addTransaction(transaction);
  };

  const handleCategorizeTransaction = async (
    transactionId: string,
    categoryId?: string
  ) => {
    await categorizeTransaction(transactionId, categoryId);
  };

  return (
    <div className="transactions-page">
      <h1>Bank Statement Analyzer</h1>

      {error && <div className="error-message">{error}</div>}

      <div className="transactions-container">
        <div className="form-container">
          <TransactionForm
            onSubmit={handleAddTransaction}
            categories={categories}
            isLoading={loading}
          />
        </div>

        <div className="table-container">
          <TransactionTable
            transactions={transactions}
            categories={categories}
            loading={loading}
            onCategorize={handleCategorizeTransaction}
          />
        </div>
      </div>
    </div>
  );
};
