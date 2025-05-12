import { ApiClient } from './ApiClient';
import { categoryClient } from './CategoryClient';
import { transactionClient } from './TransactionClient';

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    categories: categoryClient,
  };
};

export const defaultApiClient = createApiClient();
