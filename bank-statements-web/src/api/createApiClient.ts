import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    categories: categoryClient,
    statements: statementClient,
  }
}

export const defaultApiClient = createApiClient()
