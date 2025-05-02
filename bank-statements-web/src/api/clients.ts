import { transactionClient, TransactionClient } from './TransactionClient';

export interface ApiClients {
  transactionClient: TransactionClient;
}

export const apiClients: ApiClients = {
  transactionClient,
};
