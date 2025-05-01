# Bank Statements Web E2E Tests

This directory contains end-to-end tests for the Bank Statements Web application using Playwright.

## Setup

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

## Prerequisites

Before running the tests, make sure:

1. The backend API server is running:
   ```bash
   cd ../../bank-statements-api
   python run.py
   ```

2. The frontend development server is running:
   ```bash
   cd ../../bank-statements-web
   npm run dev
   ```

If the backend server is not running, the tests will fail with a connection error.

## Running Tests

```bash
# Run all tests
npm test

# Run tests with UI mode
npm run test:ui

# Run tests in headed mode (with browser visible)
npm run test:headed

# View the HTML report
npm run report
```

## Test Structure

- `tests/api-helper.ts`: Helper functions for interacting with the API
- `tests/transaction-page.spec.ts`: Tests for the Transaction Page

## Test Strategy

The tests use a combination of API calls and UI interactions to test the application:

1. Before each test, all existing transactions are deleted via the API
2. Test transactions are created via the API
3. The UI is loaded and tested to ensure it correctly displays the transactions
4. After all tests, transactions are cleaned up

This approach allows for faster and more reliable tests by using the API for setup and teardown, while still testing the UI functionality.

## Configuration

The tests are configured to run against a local development server:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1

These settings can be adjusted in:
- `playwright.config.ts`: For the frontend URL
- `tests/api-helper.ts`: For the API URL
