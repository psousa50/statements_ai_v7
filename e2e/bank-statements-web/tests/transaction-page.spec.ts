import { test, expect } from '@playwright/test';
import { createTransactions, deleteAllTransactions, getAuthCookies, testLogin } from './api-helper';

function getCurrentMonthDate(day: number): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}-${String(day).padStart(2, '0')}`;
}

test.describe('Transaction Page', () => {
  const testId = `test-${Date.now()}`;

  const testTransactions = [
    {
      date: getCurrentMonthDate(1),
      description: `Grocery Shopping (${testId})`,
      amount: -75.5,
    },
    {
      date: getCurrentMonthDate(2),
      description: `Salary Deposit (${testId})`,
      amount: 2500.0,
    },
    {
      date: getCurrentMonthDate(3),
      description: `Restaurant Bill (${testId})`,
      amount: -45.75,
    },
  ];

  test.beforeAll(async () => {
    await testLogin();
  });

  test.beforeEach(async () => {
    await deleteAllTransactions();
  });

  test('should display transactions', async ({ page }) => {
    const createdTransactions = await createTransactions(testTransactions);

    await page.context().addCookies(getAuthCookies());
    await page.goto('/');

    await page.waitForSelector('table');

    const rows = page.locator('table tbody tr');

    await page.waitForSelector('table tbody tr');

    for (const transaction of createdTransactions) {
      const formattedAmount = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(transaction.amount);

      const matchingRow = rows.filter({
        has: page.locator('td', { hasText: transaction.description }),
        hasText: formattedAmount,
      });

      await expect(matchingRow).toHaveCount(1);
    }
  });
});
