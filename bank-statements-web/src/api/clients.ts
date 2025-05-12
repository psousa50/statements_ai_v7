import { categoryClient, CategoryClient } from './CategoryClient'
import { transactionClient, TransactionClient } from './TransactionClient'

export interface ApiClients {
  transactionClient: TransactionClient
  categoryClient: CategoryClient
}

export const apiClients: ApiClients = {
  transactionClient,
  categoryClient,
}
