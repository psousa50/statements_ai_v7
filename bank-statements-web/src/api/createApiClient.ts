import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { accountClient } from './AccountClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'
import { transactionCategorizationClient } from './TransactionCategorizationClient'
import { enhancementRuleClient } from './EnhancementRuleClient'
import { descriptionGroupClient } from './DescriptionGroupClient'

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    transactionCategorizations: transactionCategorizationClient,
    enhancementRules: enhancementRuleClient,
    categories: categoryClient,
    statements: statementClient,
    accounts: accountClient,
    descriptionGroups: descriptionGroupClient,
  }
}

export const defaultApiClient = createApiClient()
