import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionsPage } from '@/pages/Transactions';
import { ApiProvider } from '@/api/ApiContext';
import { ApiClient } from '@/api/ApiClient';
import { createMockApiClient } from '@/api/createMockApiClient';
import {
  Category,
  Transaction,
  TransactionListResponse,
} from '@/types/Transaction';
import { CategoryListResponse } from '@/api/CategoryClient';

const transaction: Transaction = {
  id: '1',
  date: '2023-01-01',
  description: 'Sample Transaction',
  amount: 100,
  created_at: '2023-01-01T00:00:00Z',
  categorization_status: 'UNCATEGORIZED',
};

test('renders transactions page with mock data', async () => {
  const apiClient = createMockApiClient({
    transactions: {
      getAll: () =>
        Promise.resolve({
          transactions: [
            {
              id: '1',
              date: '2023-01-01',
              description: 'Test Transaction',
              amount: 100,
              created_at: '2023-01-01T00:00:00Z',
              categorization_status: 'UNCATEGORIZED',
            },
          ],
          total: 1,
        }),
    },
  });

  render(
    <ApiProvider client={apiClient}>
      <TransactionsPage />
    </ApiProvider>
  );

  // Check that the page title is rendered
  expect(screen.getByText('Bank Statement Analyzer')).toBeInTheDocument();

  // Wait for the transaction to be loaded and displayed
  expect(await screen.findByText('Test Transaction')).toBeInTheDocument();
});
