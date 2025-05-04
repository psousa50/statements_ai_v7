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
    const createdTransactions = await createTransactions(testTransactions);

    await page.goto('/');

    await page.waitForSelector('table');

    const rows = page.locator('table tbody tr');

    await page.waitForSelector('table tbody tr');

    for (const transaction of createdTransactions) {
      const formattedAmount = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(transaction.amount);

      const date = new Date(transaction.date);
      const month = date.toLocaleString('en-US', { month: 'short' });
      const day = date.getDate().toString().padStart(2, '0');
      const year = date.getFullYear();
      const formattedDate = `${month} ${day}, ${year}`;

      const matchingRow = rows.filter({
        has: page.locator('td', { hasText: transaction.description }),
        hasText: formattedAmount,
      });

      await expect(matchingRow).toHaveCount(1);
    }
  });
});
