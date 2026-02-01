import { ApiClient } from './ApiClient'
import { categoryClient } from './CategoryClient'
import { accountClient } from './AccountClient'
import { statementClient } from './StatementClient'
import { transactionClient } from './TransactionClient'
import { transactionCategorizationClient } from './TransactionCategorizationClient'
import { enhancementRuleClient } from './EnhancementRuleClient'
import { descriptionGroupClient } from './DescriptionGroupClient'
import { subscriptionClient } from './SubscriptionClient'
import { createChatClient } from './ChatClient'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const createApiClient = (): ApiClient => {
  return {
    transactions: transactionClient,
    transactionCategorizations: transactionCategorizationClient,
    enhancementRules: enhancementRuleClient,
    categories: categoryClient,
    statements: statementClient,
    accounts: accountClient,
    descriptionGroups: descriptionGroupClient,
    subscription: subscriptionClient,
    chatClient: createChatClient(BASE_URL),
  }
}

export const defaultApiClient = createApiClient()
