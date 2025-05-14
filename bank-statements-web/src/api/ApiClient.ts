import { CategoryClient } from './CategoryClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'

export interface ApiClient {
  transactions: TransactionClient
  categories: CategoryClient
  statements: StatementClient
}
