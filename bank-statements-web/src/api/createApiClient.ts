import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { sourceClient } from './SourceClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'
import { transactionCategorizationClient } from './TransactionCategorizationClient'

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    transactionCategorizations: transactionCategorizationClient,
    categories: categoryClient,
    statements: statementClient,
    sources: sourceClient,
  }
}

export const defaultApiClient = createApiClient()
