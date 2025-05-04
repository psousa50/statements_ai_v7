import axios from 'axios';

// Define the Transaction interface based on the project's type definition
interface Transaction {
  id?: string;
  date: string;
  description: string;
  amount: number;
  created_at?: string;
}

// API base URL - this should match the backend API URL
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;

/**
 * Creates a new transaction via the API
 * @param transaction Transaction data to create
 * @returns The created transaction
 */
export async function createTransaction(
  transaction: Omit<Transaction, 'id' | 'created_at'>
): Promise<Transaction> {
  try {
    const response = await axios.post(
      `${API_V1_BASE_URL}/transactions`,
      transaction
    );
    return response.data;
  } catch (error: any) {
    if (error.code === 'ECONNREFUSED') {
      console.error(
        'ERROR: API server is not running. Please start the backend server with "cd bank-statements-api && python run.py" before running tests.'
      );
    } else {
      console.error('Error creating transaction:', error);
    }
    throw error; // Re-throw to allow the test to fail if transaction creation fails
  }
}

/**
 * Creates multiple transactions via the API
 * @param transactions Array of transaction data to create
 * @returns Array of created transactions
 */
export async function createTransactions(
  transactions: Omit<Transaction, 'id' | 'created_at'>[]
): Promise<Transaction[]> {
  try {
    const createdTransactions: Transaction[] = [];

    for (const transaction of transactions) {
      try {
        const createdTransaction = await createTransaction(transaction);
        createdTransactions.push(createdTransaction);
      } catch (error) {
        console.error(`Error creating transaction:`, error);
        console.error(
          `Failed to create transaction: ${JSON.stringify(transaction)}`
        );
        // Continue with the next transaction
      }
    }

    if (createdTransactions.length === 0) {
      throw new Error('Failed to create any transactions');
    }

    return createdTransactions;
  } catch (error) {
    console.error('Error creating transactions:', error);
    throw error;
  }
}

/**
 * Deletes all transactions from the API
 * This is useful for cleaning up before and after tests
 */
export async function deleteAllTransactions(): Promise<void> {
  try {
    const response = await axios.get(`${API_V1_BASE_URL}/transactions`);
    const transactions: Transaction[] = response.data.transactions;

    const deletePromises = transactions.map(
      async (transaction) =>
        await axios.delete(`${API_V1_BASE_URL}/transactions/${transaction.id}`)
    );

    await Promise.all(deletePromises);
  } catch (error: any) {
    if (error.code === 'ECONNREFUSED') {
      console.error(
        'ERROR: API server is not running. Please start the backend server with "cd bank-statements-api && python run.py" before running tests.'
      );
    } else {
      console.error('Error deleting transactions:', error);
    }
  } finally {
    console.log('Delete all transactions process completed.');
  }
}
