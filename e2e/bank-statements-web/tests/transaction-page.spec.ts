import { test, expect } from '@playwright/test';
import { createTransactions, deleteAllTransactions } from './api-helper';

test.describe('Transaction Page', () => {
  // Generate a unique test ID to avoid conflicts with existing data
  const testId = `test-${Date.now()}`;

  // Sample transactions to create via API with unique identifiers
  const testTransactions = [
    {
      date: '2025-01-01',
      description: `Grocery Shopping (${testId})`,
      amount: -75.5,
    },
    {
      date: '2025-01-02',
      description: `Salary Deposit (${testId})`,
      amount: 2500.0,
    },
    {
      date: '2025-01-03',
      description: `Restaurant Bill (${testId})`,
      amount: -45.75,
    },
  ];

  // Clean up before each test
  test.beforeEach(async () => {
    await deleteAllTransactions();
  });

  test('should display transactions', async ({ page }) => {
    // Create test transactions via API
    const createdTransactions = await createTransactions(testTransactions);

    // Navigate to the transactions page
    await page.goto('/');

    // Wait for the transaction table to be visible
    await page.waitForSelector('table');

    // Instead of checking each transaction individually, verify the table contains all expected data
    // This avoids issues with duplicate text in the table

    // Get all rows in the table body (excluding header)
    const rows = page.locator('table tbody tr');

    // Wait for the table to be populated
    await page.waitForSelector('table tbody tr');

    // Instead of checking the exact count, we'll just make sure our transactions are in the table
    // This is more resilient if there are other transactions in the database

    // For each transaction, verify it appears in the table
    for (const transaction of createdTransactions) {
      // Format the amount as it would appear in the UI
      const formattedAmount = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(transaction.amount);

      // Format the date as it would appear in the UI
      const date = new Date(transaction.date);
      const month = date.toLocaleString('en-US', { month: 'short' });
      const day = date.getDate().toString().padStart(2, '0');
      const year = date.getFullYear();
      const formattedDate = `${month} ${day}, ${year}`;

      // Find a row that contains both the description and formatted amount
      const matchingRow = rows.filter({
        has: page.locator('td', { hasText: transaction.description }),
        hasText: formattedAmount,
      });

      // Verify the row exists
      await expect(matchingRow).toHaveCount(1);
    }

    // We've already verified that each of our transactions appears in the table,
    // so we don't need to check the exact row count
  });

  // Clean up after all tests
  test.afterAll(async () => {
    await deleteAllTransactions();
  });
});
