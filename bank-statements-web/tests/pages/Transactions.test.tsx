import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionsPage } from '../../src/pages/Transactions';
import { ApiClientsProvider } from '../../src/api/ApiClientsContext';
import { ApiClients } from '../../src/api/clients';
import {
  Transaction,
  TransactionListResponse,
} from '../../src/types/Transaction';

// Default mock implementation for transactionClient

const transaction: Transaction = {
  id: '1',
  date: '2023-01-01',
  description: 'Sample Transaction',
  amount: 100,
  created_at: '2023-01-01T00:00:00Z',
};

const defaultTransactionClient = {
  getAll: () =>
    Promise.resolve({
      transactions: [transaction],
      total: 1,
    } as TransactionListResponse),
  getById: () => Promise.resolve(transaction),
  create: () => Promise.resolve(transaction),
  update: () => Promise.resolve(transaction),
  delete: () => Promise.resolve(),
};

const defaultApiClients: ApiClients = {
  transactionClient: defaultTransactionClient,
};

const createApiClients = (overrides: Partial<ApiClients> = {}): ApiClients => ({
  ...defaultApiClients,
  ...overrides,
});

test('renders transactions page with mock data', async () => {
  const apiClients: ApiClients = createApiClients({
    transactionClient: {
      ...defaultTransactionClient,
      getAll: () =>
        Promise.resolve({
          transactions: [
            {
              id: '1',
              date: '2023-01-01',
              description: 'Test Transaction',
              amount: 100,
              created_at: '2023-01-01T00:00:00Z',
            },
          ],
          total: 1,
        } as TransactionListResponse),
    },
  });

  render(
    <ApiClientsProvider clients={apiClients}>
      <TransactionsPage />
    </ApiClientsProvider>
  );

  // Check that the page title is rendered
  expect(screen.getByText('Bank Statement Analyzer')).toBeInTheDocument();

  // Wait for the transaction to be loaded and displayed
  expect(await screen.findByText('Test Transaction')).toBeInTheDocument();
});
