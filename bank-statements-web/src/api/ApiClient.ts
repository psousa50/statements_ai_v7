import { CategoryClient } from './CategoryClient'
import { SourceClient } from './SourceClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'
import { TransactionCategorizationClient } from './TransactionCategorizationClient'

export interface ApiClient {
  transactions: TransactionClient
  transactionCategorizations: TransactionCategorizationClient
  categories: CategoryClient
  statements: StatementClient
  sources: SourceClient
}
