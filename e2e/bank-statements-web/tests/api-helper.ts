import { APIRequestContext, request } from "@playwright/test";

// Define the Transaction interface based on the project's type definition
interface Transaction {
  id: string;
  description: string;
  amount: number;
  date: string;
  category_id?: string;
  source_id: string;
  created_at: string;
  updated_at: string;
}

// Get API URL from environment or use default
const API_BASE_URL =
  process.env.VITE_API_URL ||
  process.env.API_BASE_URL ||
  "http://localhost:8000";
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;

export async function createApiContext(): Promise<APIRequestContext> {
  return await request.newContext({
    baseURL: API_BASE_URL,
  });
}

/**
 * Creates a single transaction via the API
 * @param transaction The transaction data (without id and created_at)
 * @returns The created transaction
 */
export async function createTransactionLegacy(
  transaction: Omit<Transaction, "id" | "created_at">
): Promise<Transaction> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/transactions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transaction),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    console.error("Error creating transaction:", error);
    throw error;
  }
}

/**
 * Creates multiple transactions via the API
 * @param transactions Array of transaction data (without id and created_at)
 * @returns Array of created transactions
 */
export async function createTransactions(
  transactions: Omit<Transaction, "id" | "created_at">[]
): Promise<Transaction[]> {
  try {
    const createdTransactions: Transaction[] = [];

    for (const transaction of transactions) {
      try {
        const createdTransaction = await createTransactionLegacy(transaction);
        createdTransactions.push(createdTransaction);
      } catch (error) {
        console.error(
          `Failed to create transaction: ${transaction.description}`,
          error
        );
      }
    }

    return createdTransactions;
  } catch (error: any) {
    console.error("Error creating transactions:", error);
    throw error;
  }
}

/**
 * Deletes all transactions via the API
 * This is useful for cleaning up before and after tests
 */
export async function deleteAllTransactions(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/transactions`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const transactions: Transaction[] = data.transactions;

    const deletePromises = transactions.map(
      async (transaction) =>
        await fetch(`${API_BASE_URL}/api/v1/transactions/${transaction.id}`, {
          method: "DELETE",
        })
    );

    await Promise.all(deletePromises);
    console.log(`Deleted ${transactions.length} transactions`);
  } catch (error: any) {
    console.error("Error deleting transactions:", error);
    throw error;
  }
}

export async function getTransactions(apiContext: APIRequestContext) {
  const response = await apiContext.get("/api/v1/transactions");
  return await response.json();
}

export async function deleteTransaction(
  apiContext: APIRequestContext,
  transactionId: string
) {
  return await apiContext.delete(`/api/v1/transactions/${transactionId}`);
}
