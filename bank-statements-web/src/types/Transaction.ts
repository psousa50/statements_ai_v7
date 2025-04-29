export interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  created_at: string;
}

export interface TransactionCreate {
  date: string;
  description: string;
  amount: number;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
}
