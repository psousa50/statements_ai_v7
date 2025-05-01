# Bank Statements API Tests

This directory contains tests for the Bank Statements API project.

## Test Structure

The tests are organized as follows:

```
tests/
├── conftest.py             # Common fixtures for all tests
├── __init__.py             # Package marker
└── unit/                   # Unit tests
    ├── __init__.py         # Package marker
    └── services/           # Tests for service layer
        ├── __init__.py     # Package marker
        ├── test_transaction.py                # Tests for TransactionService
        └── test_transaction_with_fixtures.py  # Alternative tests using common fixtures
```

## Running Tests

To run all tests:

```bash
cd bank-statements-api
pytest
```

To run specific tests:

```bash
# Run all service tests
pytest tests/unit/services/

# Run a specific test file
pytest tests/unit/services/test_transaction.py

# Run a specific test function
pytest tests/unit/services/test_transaction.py::TestTransactionService::test_create_transaction
```

## Test Coverage

To run tests with coverage:

```bash
# Run tests with coverage for a specific module
pytest --cov=app.services.transaction tests/

# Run tests with coverage for the entire app
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
```

The HTML coverage report will be generated in the `htmlcov` directory. Open `htmlcov/index.html` in a browser to view the detailed coverage report.

Current coverage results:
- TransactionService: 100% coverage
- Overall app: 70% coverage

## Mocking Strategy

The tests use pytest fixtures and unittest.mock to create mock objects for dependencies. This allows testing the service layer in isolation without requiring a database connection.

For example, the TransactionService tests mock the TransactionRepository to avoid actual database interactions.

## Adding New Tests

When adding new tests:

1. Follow the existing directory structure
2. Use fixtures from conftest.py where appropriate
3. Use the unittest.mock library to mock dependencies
4. Follow the Arrange-Act-Assert pattern in test methods

## Test Naming Conventions

- Test files should be named `test_*.py`
- Test classes should be named `Test*`
- Test methods should be named `test_*`
- Test method names should describe what they're testing
