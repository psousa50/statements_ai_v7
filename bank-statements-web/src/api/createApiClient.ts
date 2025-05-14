import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { sourceClient } from './SourceClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    categories: categoryClient,
    statements: statementClient,
    sources: sourceClient,
  }
}

export const defaultApiClient = createApiClient()
