import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { accountClient } from './AccountClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'
import { transactionCategorizationClient } from './TransactionCategorizationClient'

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    transactionCategorizations: transactionCategorizationClient,
    categories: categoryClient,
    statements: statementClient,
    accounts: accountClient,
  }
}

export const defaultApiClient = createApiClient()
