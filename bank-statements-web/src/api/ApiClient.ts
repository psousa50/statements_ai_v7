import { CategoryClient } from './CategoryClient'
import { SourceClient } from './SourceClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'

export interface ApiClient {
  transactions: TransactionClient
  categories: CategoryClient
  statements: StatementClient
  sources: SourceClient
}
