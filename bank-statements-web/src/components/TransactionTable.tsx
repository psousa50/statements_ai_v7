import { format } from 'date-fns';
import { Transaction } from '../types/Transaction';

interface TransactionTableProps {
  transactions: Transaction[];
  loading: boolean;
}

export const TransactionTable = ({
  transactions,
  loading,
}: TransactionTableProps) => {
  if (loading) {
    return <div className="loading">Loading transactions...</div>;
  }

  if (transactions.length === 0) {
    return (
      <div className="no-data">
        No transactions found. Add one to get started!
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch (error) {
      return dateString;
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="transaction-table">
      <h2>Transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{formatDate(transaction.date)}</td>
              <td>{transaction.description}</td>
              <td className={transaction.amount < 0 ? 'negative' : 'positive'}>
                {formatAmount(transaction.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
