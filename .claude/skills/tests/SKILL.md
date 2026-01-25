---
name: tests
description: Explains this project's testing patterns, structure, and how to write tests
---

# Testing Guide

## Frameworks

### Backend (Python/FastAPI)
- **pytest** - Test runner with markers for integration tests
- **pytest-cov** - Coverage reporting
- **unittest.mock** - Mocking dependencies

### Frontend (React/TypeScript)
- **Vitest** - Unit test runner (configured in `vite.config.ts`)
- **@testing-library/react** - Component testing
- **@testing-library/user-event** - User interaction simulation
- **jsdom** - DOM environment

### E2E
- **Playwright** - Browser automation (Chromium, Firefox, WebKit)

## Structure

```
bank-statements-api/
  tests/
    conftest.py                      # Common fixtures (test_user, sample_transaction, mock repos)
    unit/
      common/                        # Utility tests (text normalization)
      domain/                        # Domain model tests
      services/                      # Service layer tests
        schema_detection/
        statement_processing/
      adapters/repositories/         # Repository tests
    integration/
      conftest.py                    # DB fixtures (engine, session, user_a/b, accounts)
      test_multi_tenancy.py          # Multi-user isolation tests
      test_statement_upload_integration.py

bank-statements-web/
  tests/
    setupTests.ts                    # Global setup (jest-dom, IntersectionObserver mock)
    createMockApiClient.ts           # API client factory for mocking
    pages/
      Transactions.test.tsx

e2e/bank-statements-web/
  playwright.config.ts
  tests/
    api-helper.ts                    # Auth helpers, transaction CRUD
    transaction-page.spec.ts
```

## Running Tests

```bash
# All tests
pnpm test

# Backend only
pnpm test:api                        # Unit + integration
pnpm test:api:unit                   # Unit only
pnpm test:api:unit:cov               # With coverage

# Frontend only
pnpm test:web                        # Vitest (run once)
pnpm test:web:unit:watch             # Watch mode
pnpm test:web:unit:ui                # Vitest UI

# E2E
pnpm test:e2e                        # Headless
pnpm test:e2e:ui                     # Playwright UI mode

# Integration DB setup
pnpm test:db:up                      # Start test DB (port 15432)
pnpm test:db:migrate                 # Run migrations
```

## Writing Tests

### Backend Unit Tests

Use class-based tests with `setup_method` for helper factories:

```python
class TestTransactionEnhancer:
    def setup_method(self) -> None:
        self.enhancer = TransactionEnhancer()

    def create_transaction(self, normalized_description="test", amount=Decimal("100.00")):
        transaction = Transaction()
        transaction.id = uuid4()
        transaction.normalized_description = normalized_description
        transaction.amount = amount
        return transaction

    def test_exact_match_rule_applies(self):
        category_id = uuid4()
        transaction = self.create_transaction(normalized_description="starbucks coffee")
        rule = self.create_rule(pattern="starbucks coffee", match_type=MatchType.EXACT, category_id=category_id)

        result = self.enhancer.apply_rules([transaction], [rule])

        assert len(result) == 1
        assert result[0].category_id == category_id
```

### Backend Integration Tests

Use fixtures from `tests/integration/conftest.py`:

```python
def test_user_can_only_see_own_accounts(self, db_session, user_a, user_b, account_for_user_a):
    repo = SQLAlchemyAccountRepository(db_session)
    user_a_accounts = repo.get_all(user_a.id)
    assert len(user_a_accounts) == 1
```

### Frontend Unit Tests

Use `createMockApiClient` with method overrides:

```typescript
const renderTransactionsPage = (options: RenderOptions = {}) => {
  const apiClient = createMockApiClient({
    transactions: {
      getAll: vi.fn().mockResolvedValue(transactions),
    },
  })

  render(
    <QueryClientProvider client={createTestQueryClient()}>
      <MemoryRouter>
        <ApiProvider client={apiClient}>
          <TransactionsPage />
        </ApiProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )

  return { apiClient, user: userEvent.setup() }
}

test('displays transaction in list', async () => {
  renderTransactionsPage({ transactions: createPaginatedResponse([transaction]) })
  expect(await screen.findByText('Coffee Shop')).toBeInTheDocument()
})
```

### E2E Tests

Use `testLogin()` for auth, clean up with `deleteAllTransactions()`:

```typescript
test.beforeAll(async () => {
  await testLogin()
})

test.beforeEach(async () => {
  await deleteAllTransactions()
})

test('should display transactions', async ({ page }) => {
  await createTransactions(testTransactions)
  await page.context().addCookies(getAuthCookies())
  await page.goto('/')
  await expect(page.locator('table tbody tr')).toHaveCount(3)
})
```

## Mocking

### Backend

Use `unittest.mock.MagicMock` with repository specs:

```python
@pytest.fixture
def mock_transaction_repository():
    return MagicMock(spec=TransactionRepository)
```

### Frontend

`createMockApiClient` provides default implementations for all API methods. Override specific methods:

```typescript
const apiClient = createMockApiClient({
  transactions: {
    getAll: vi.fn().mockRejectedValue(new Error('Network error')),
  },
})
```

## Test Utilities

### Backend Fixtures (`tests/conftest.py`)
- `test_user_id` / `test_user` - User fixtures
- `sample_transaction_data` / `sample_transaction` - Transaction fixtures
- `mock_transaction_repository` - Mocked repository

### Integration Fixtures (`tests/integration/conftest.py`)
- `engine` / `tables` / `db_session` - Database setup with rollback
- `user_a` / `user_b` - Two test users
- `account_for_user_a` / `account_for_user_b` - Accounts per user
- `category_for_user_a` / `category_for_user_b` - Categories per user

### Frontend Utilities (`tests/createMockApiClient.ts`)
- `createMockApiClient()` - Full API client mock factory
- Default implementations for all endpoints
- Override any method with vi.fn()

### E2E Helpers (`e2e/bank-statements-web/tests/api-helper.ts`)
- `testLogin()` - Authenticate test user
- `getAuthCookies()` - Get cookies for page context
- `createTransaction()` / `createTransactions()` - Create test data
- `deleteAllTransactions()` - Clean up

## Coverage

### Backend
```bash
pnpm test:api:unit:cov
pytest --cov=app --cov-report=html tests/
```
HTML report generated in `htmlcov/`.

### Frontend
```bash
pnpm test:web
```
Vitest coverage configured with v8 provider. Reports: text, json, html.

Config in `vite.config.ts`:
```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html'],
  include: ['src/**/*'],
  exclude: ['src/**/*.test.ts', 'src/**/*.test.tsx', 'src/main.tsx'],
}
```

## Naming Conventions

- **Files**: `test_*.py` (backend), `*.test.tsx` (frontend), `*.spec.ts` (e2e)
- **Classes**: `Test*` (backend)
- **Methods/Functions**: `test_*` (describe what's being tested)
