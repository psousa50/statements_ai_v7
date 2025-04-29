import { useTransactions } from '../services/hooks/useTransactions';
import { TransactionForm } from '../components/TransactionForm';
import { TransactionTable } from '../components/TransactionTable';
import { TransactionCreate } from '../types/Transaction';

export const TransactionsPage = () => {
  const { transactions, loading, error, addTransaction } = useTransactions();

  const handleAddTransaction = async (transaction: TransactionCreate) => {
    await addTransaction(transaction);
  };

  return (
    <div className="transactions-page">
      <h1>Bank Statement Analyzer</h1>

      {error && <div className="error-message">{error}</div>}

      <div className="transactions-container">
        <div className="form-container">
          <TransactionForm
            onSubmit={handleAddTransaction}
            isLoading={loading}
          />
        </div>

        <div className="table-container">
          <TransactionTable transactions={transactions} loading={loading} />
        </div>
      </div>
    </div>
  );
};
