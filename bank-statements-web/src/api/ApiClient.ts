import { CategoryClient } from './CategoryClient'
import { AccountClient } from './AccountClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'
import { TransactionCategorizationClient } from './TransactionCategorizationClient'

export interface ApiClient {
  transactions: TransactionClient
  transactionCategorizations: TransactionCategorizationClient
  categories: CategoryClient
  statements: StatementClient
  accounts: AccountClient
}
