import { APIRequestContext, request } from "@playwright/test";

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

const API_BASE_URL =
  process.env.VITE_API_URL ||
  process.env.API_BASE_URL ||
  "http://localhost:8010";
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;

interface CookieData {
  name: string;
  value: string;
  domain: string;
  path: string;
}

let authCookies: string = "";
let parsedCookies: CookieData[] = [];
let testAccountId: string = "";

export async function testLogin(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Test login failed: ${response.status}`);
  }

  const data = await response.json();
  testAccountId = data.account_id;

  const setCookieHeader = response.headers.get("set-cookie");
  if (setCookieHeader) {
    const cookieParts = setCookieHeader.split(",").map((c) => c.trim());
    const cookies: CookieData[] = [];

    for (const part of cookieParts) {
      const [nameValue] = part.split(";");
      const [name, value] = nameValue.split("=");
      if (name && value) {
        cookies.push({
          name: name.trim(),
          value: value.trim(),
          domain: "localhost",
          path: "/",
        });
      }
    }

    parsedCookies = cookies;
    authCookies = cookies.map((c) => `${c.name}=${c.value}`).join("; ");
  }
}

export function getAuthCookies(): CookieData[] {
  return parsedCookies;
}

export function getTestAccountId(): string {
  return testAccountId;
}

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (authCookies) {
    headers["Cookie"] = authCookies;
  }
  return headers;
}

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
export async function createTransaction(
  transaction: Omit<Transaction, "id" | "created_at" | "source_id" | "updated_at">
): Promise<Transaction> {
  try {
    const payload = {
      ...transaction,
      account_id: testAccountId,
    };
    const response = await fetch(`${API_BASE_URL}/api/v1/transactions`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
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
        const createdTransaction = await createTransaction(transaction);
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
    const response = await fetch(`${API_BASE_URL}/api/v1/transactions`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const transactions: Transaction[] = data.transactions;

    const deletePromises = transactions.map(
      async (transaction) =>
        await fetch(`${API_BASE_URL}/api/v1/transactions/${transaction.id}`, {
          method: "DELETE",
          headers: getAuthHeaders(),
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
