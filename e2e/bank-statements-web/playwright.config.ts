import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for Bank Statements Web E2E tests
 *
 * Note: These tests require the backend API server to be running separately.
 * The webServer configuration below only starts the frontend development server.
 *
 * To start the backend server:
 * cd ../../bank-statements-api && python run.py
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL:
      process.env.PLAYWRIGHT_TEST_BASE_URL ||
      process.env.WEB_BASE_URL ||
      "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],
  webServer: {
    command: "pnpm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
