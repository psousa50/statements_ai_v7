import { CategoryClient } from './CategoryClient'
import { TransactionClient } from './TransactionClient'

export interface ApiClient {
  transactions: TransactionClient
  categories: CategoryClient
}
