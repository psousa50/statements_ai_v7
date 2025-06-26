import { CategoryClient } from './CategoryClient'
import { AccountClient } from './AccountClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'
import { TransactionCategorizationClient } from './TransactionCategorizationClient'
import { EnhancementRuleClient } from './EnhancementRuleClient'

export interface ApiClient {
  transactions: TransactionClient
  transactionCategorizations: TransactionCategorizationClient
  enhancementRules: EnhancementRuleClient
  categories: CategoryClient
  statements: StatementClient
  accounts: AccountClient
}
